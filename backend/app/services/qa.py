from __future__ import annotations

from typing import Any, Literal

import duckdb

from app.db import SCHEMA_DESCRIPTION
from app.interpreters.base import Abstain, QuestionInterpreter, TemplateChoice
from app.interpreters.keyword import KeywordBaselineInterpreter
from app.models import Provenance, QaResponse, TableCoverage
from app.services.coverage import coverage_for_table
from app.templates.catalog import TEMPLATE_BY_ID, catalog_for_llm, run_template


def _summarize_grounded(template_id: str, rows: list[dict[str, Any]]) -> str:
    n = len(rows)
    name = TEMPLATE_BY_ID[template_id].name
    if template_id == "event_ordering":
        return (
            f"Grounded Answer from template '{name}': compared the earliest matching "
            "timestamp for each side (earliest-match rule when multiple rows match a label). "
            f"{n} row(s) retrieved from the structured record."
        )
    return f"Grounded Answer from template '{name}': {n} row(s) retrieved from the structured record."


def _summarize_no_data(template_id: str, coverage: TableCoverage) -> str:
    name = TEMPLATE_BY_ID[template_id].name
    cov = (
        f"Patient coverage for `{coverage.table}`: "
        f"{'has rows' if coverage.has_rows else 'no rows'} "
        f"(row_count={coverage.row_count})."
    )
    return (
        f"No-Data Answer: template '{name}' ran successfully but returned zero rows. {cov} "
        "This reports absence of matching rows in the queried table — not a clinical negative."
    )


def answer_question(
    con: duckdb.DuckDBPyConnection,
    question: str,
    subject_id: int,
    hadm_id: int | None,
    interpreter: QuestionInterpreter,
    allow_keyword_rescue: bool = True,
) -> QaResponse:
    catalog = catalog_for_llm()
    interpreter_used: Literal["llm", "keyword", "keyword_rescue", "fake"]
    raw_name = getattr(interpreter, "name", "fake")

    try:
        result = interpreter.interpret(question, SCHEMA_DESCRIPTION, catalog)
        interpreter_used = raw_name if raw_name in ("llm", "keyword", "fake") else "fake"
    except Exception:
        if not allow_keyword_rescue or raw_name != "llm":
            raise
        result = KeywordBaselineInterpreter().interpret(question, SCHEMA_DESCRIPTION, catalog)
        interpreter_used = "keyword_rescue"

    if isinstance(result, Abstain):
        return QaResponse(
            kind="abstention",
            question=question,
            subject_id=subject_id,
            hadm_id=hadm_id,
            summary=f"Abstention: {result.reason}",
            interpreter=interpreter_used,
            abstention_reason=result.reason,
        )

    assert isinstance(result, TemplateChoice)
    slots = dict(result.slots)
    # Request context wins over LLM/keyword slot junk (e.g. hadm_id="").
    if hadm_id is not None:
        slots["hadm_id"] = hadm_id
    elif slots.get("hadm_id") in ("", None):
        slots.pop("hadm_id", None)

    try:
        tr = run_template(con, result.template_id, subject_id, hadm_id, slots)
    except Exception as exc:
        raise ValueError(str(exc)) from exc

    coverage = coverage_for_table(con, subject_id, tr.coverage_table)

    if not tr.rows:
        return QaResponse(
            kind="no_data",
            question=question,
            subject_id=subject_id,
            hadm_id=hadm_id,
            summary=_summarize_no_data(result.template_id, coverage),
            rows=[],
            provenance=[],
            coverage=[coverage],
            template_id=result.template_id,
            slots=slots,
            sql=tr.sql,
            interpreter=interpreter_used,
        )

    # Ensure every row-backed fact has provenance (invariant)
    provenance: list[Provenance] = list(tr.provenance)
    return QaResponse(
        kind="grounded",
        question=question,
        subject_id=subject_id,
        hadm_id=hadm_id,
        summary=_summarize_grounded(result.template_id, tr.rows),
        rows=tr.rows,
        provenance=provenance,
        coverage=[coverage],
        template_id=result.template_id,
        slots=slots,
        sql=tr.sql,
        interpreter=interpreter_used,
    )
