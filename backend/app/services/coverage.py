"""Per-Patient table coverage — first-class for No-Data Answers."""

from __future__ import annotations

import duckdb

from app.db import fetchall_dicts, fetchone_dict
from app.models import TableCoverage

COVERAGE_TABLES = [
    ("emar", "Medication administrations (eMAR); present for 65 of 100 Patients"),
    ("labevents", "Laboratory results"),
    ("microbiologyevents", "Microbiology events"),
    ("procedures_icd", "Hospital procedure codes"),
    ("chartevents", "ICU charted observations"),
    ("transfers", "Ward/unit transfers"),
    ("diagnoses_icd", "Billed ICD diagnoses"),
    ("drgcodes", "DRG codes"),
]


def patient_coverage(con: duckdb.DuckDBPyConnection, subject_id: int) -> list[TableCoverage]:
    out: list[TableCoverage] = []
    for table, note in COVERAGE_TABLES:
        row = fetchone_dict(
            con,
            f"SELECT COUNT(*) AS n FROM {table} WHERE subject_id = ?",
            [subject_id],
        )
        n = int(row["n"]) if row else 0
        out.append(TableCoverage(table=table, has_rows=n > 0, row_count=n, note=note))
    return out


def all_patients_coverage(
    con: duckdb.DuckDBPyConnection,
) -> dict[int, list[TableCoverage]]:
    """Batch coverage for every Patient — one GROUP BY per table."""
    counts: dict[int, dict[str, int]] = {}
    for table, _note in COVERAGE_TABLES:
        rows = fetchall_dicts(
            con,
            f"SELECT subject_id, COUNT(*) AS n FROM {table} GROUP BY subject_id",
        )
        for r in rows:
            sid = int(r["subject_id"])
            counts.setdefault(sid, {})[table] = int(r["n"])

    # Ensure all patients appear (even with zero coverage)
    patient_ids = [
        int(r["subject_id"]) for r in fetchall_dicts(con, "SELECT subject_id FROM patients")
    ]
    result: dict[int, list[TableCoverage]] = {}
    for sid in patient_ids:
        cov: list[TableCoverage] = []
        for table, note in COVERAGE_TABLES:
            n = counts.get(sid, {}).get(table, 0)
            cov.append(TableCoverage(table=table, has_rows=n > 0, row_count=n, note=note))
        result[sid] = cov
    return result


def coverage_for_table(
    con: duckdb.DuckDBPyConnection, subject_id: int, table: str
) -> TableCoverage:
    note = next((n for t, n in COVERAGE_TABLES if t == table), None)
    row = fetchone_dict(
        con,
        f"SELECT COUNT(*) AS n FROM {table} WHERE subject_id = ?",
        [subject_id],
    )
    n = int(row["n"]) if row else 0
    return TableCoverage(table=table, has_rows=n > 0, row_count=n, note=note)
