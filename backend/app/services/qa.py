from __future__ import annotations

from typing import Any, Literal

import duckdb

from app.db import SCHEMA_DESCRIPTION
from app.interpreters.base import Abstain, QuestionInterpreter, TemplateChoice
from app.interpreters.keyword import KeywordBaselineInterpreter  # also used as LLM fallback
from app.models import Provenance, QaResponse, TableCoverage
from app.services.coverage import coverage_for_table
from app.templates.catalog import TEMPLATE_BY_ID, catalog_for_llm, run_template


def _summarize_grounded(template_id: str, rows: list[dict[str, Any]]) -> str:
    n = len(rows)
    name = TEMPLATE_BY_ID[template_id].name
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
    allow_keyword_fallback: bool = True,
) -> QaResponse:
    catalog = catalog_for_llm()
    interpreter_used: Literal["llm", "keyword", "keyword_fallback", "fake"]
    raw_name = getattr(interpreter, "name", "fake")

    try:
        result = interpreter.interpret(question, SCHEMA_DESCRIPTION, catalog)
        interpreter_used = raw_name if raw_name in ("llm", "keyword", "fake") else "fake"
    except Exception as exc:  # noqa: BLE001
        if not allow_keyword_fallback or raw_name == "keyword":
            raise
        result = KeywordBaselineInterpreter().interpret(question, SCHEMA_DESCRIPTION, catalog)
        interpreter_used = "keyword_fallback"
        _ = exc

    # If the LLM abstains as "no template" but the keyword baseline can route safely,
    # prefer the baseline (labeled) rather than refusing an in-scope question.
    if (
        isinstance(result, Abstain)
        and result.trigger == "no_template"
        and allow_keyword_fallback
        and raw_name == "llm"
    ):
        kw = KeywordBaselineInterpreter().interpret(question, SCHEMA_DESCRIPTION, catalog)
        if isinstance(kw, TemplateChoice):
            result = kw
            interpreter_used = "keyword_fallback"

    if isinstance(result, Abstain):
        return QaResponse(
            kind="abstention",
            question=question,
            subject_id=subject_id,
            hadm_id=hadm_id,
            summary=f"Abstention: {result.reason}",
            interpreter=interpreter_used,
            abstention_reason=result.reason,
            is_ai_phrasing=True,
        )

    assert isinstance(result, TemplateChoice)
    tmpl = TEMPLATE_BY_ID[result.template_id]
    slots = dict(result.slots)
    if hadm_id is not None:
        slots.setdefault("hadm_id", hadm_id)

    try:
        tr = run_template(con, result.template_id, subject_id, hadm_id, slots)
    except Exception as exc:  # noqa: BLE001
        return QaResponse(
            kind="abstention",
            question=question,
            subject_id=subject_id,
            hadm_id=hadm_id,
            summary=f"Abstention: template '{result.template_id}' could not run ({exc}).",
            template_id=result.template_id,
            slots=slots,
            interpreter=interpreter_used,
            abstention_reason=str(exc),
            is_ai_phrasing=True,
        )

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
            is_ai_phrasing=True,
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
        is_ai_phrasing=True,
    )
