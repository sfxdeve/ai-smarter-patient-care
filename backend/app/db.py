"""DuckDB access over frozen MIMIC-IV Demo csv.gz files (read-only)."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import duckdb

from app.config import get_settings

# Tables we expose as views. Paths are relative to the demo root.
HOSP_TABLES = [
    "admissions",
    "patients",
    "transfers",
    "labevents",
    "d_labitems",
    "emar",
    "emar_detail",
    "microbiologyevents",
    "procedures_icd",
    "d_icd_procedures",
    "diagnoses_icd",
    "d_icd_diagnoses",
    "drgcodes",
    "services",
    "prescriptions",
    "pharmacy",
    "hcpcsevents",
]

ICU_TABLES = [
    "icustays",
    "chartevents",
    "d_items",
    "procedureevents",
    "inputevents",
    "outputevents",
    "datetimeevents",
]

# Vital-sign itemids used for ICU observation banding (common MIMIC items).
VITAL_ITEMIDS = (
    220045,  # Heart Rate
    220210,  # Respiratory Rate
    220277,  # O2 saturation pulseoxymetry
    220179,  # Non Invasive Blood Pressure systolic
    220180,  # Non Invasive Blood Pressure diastolic
    220181,  # Non Invasive Blood Pressure mean
    220050,  # Arterial Blood Pressure systolic
    220051,  # Arterial Blood Pressure diastolic
    220052,  # Arterial Blood Pressure mean
    223761,  # Temperature Fahrenheit
    223762,  # Temperature Celsius
)


def _csv_path(data_dir: Path, module: str, table: str) -> Path:
    return data_dir / module / f"{table}.csv.gz"


def connect(data_dir: Path | None = None) -> duckdb.DuckDBPyConnection:
    settings = get_settings()
    root = Path(data_dir or settings.data_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"MIMIC demo data not found at {root}")

    con = duckdb.connect(database=":memory:")
    # Read-only CSV access — never write back to source files.
    # Paths are local trusted filesystem paths; DuckDB disallows prepared
    # parameters inside CREATE VIEW ... read_csv_auto(...).
    for table in HOSP_TABLES:
        path = _csv_path(root, "hosp", table)
        if path.exists():
            escaped = str(path).replace("'", "''")
            con.execute(
                f"CREATE VIEW {table} AS SELECT * FROM read_csv_auto('{escaped}', header=true)"
            )
    for table in ICU_TABLES:
        path = _csv_path(root, "icu", table)
        if path.exists():
            escaped = str(path).replace("'", "''")
            con.execute(
                f"CREATE VIEW {table} AS SELECT * FROM read_csv_auto('{escaped}', header=true)"
            )
    return con


@contextmanager
def db_session(data_dir: Path | None = None) -> Iterator[duckdb.DuckDBPyConnection]:
    con = connect(data_dir)
    try:
        yield con
    finally:
        con.close()


def fetchall_dicts(con: duckdb.DuckDBPyConnection, sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
    cur = con.execute(sql, params or [])
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def fetchone_dict(con: duckdb.DuckDBPyConnection, sql: str, params: list[Any] | None = None) -> dict[str, Any] | None:
    rows = fetchall_dicts(con, sql, params)
    return rows[0] if rows else None


SCHEMA_DESCRIPTION = """
MIMIC-IV Demo tables (subject_id = Patient, hadm_id = Admission, stay_id = ICU Stay):
- patients(subject_id, gender, anchor_age, anchor_year, anchor_year_group, dod)
- admissions(subject_id, hadm_id, admittime, dischtime, deathtime, admission_type, admission_location, discharge_location, ...)
- transfers(subject_id, hadm_id, transfer_id, eventtype, careunit, intime, outtime)
- labevents(labevent_id, subject_id, hadm_id, itemid, charttime, value, valuenum, valueuom, flag) + d_labitems(itemid, label, fluid, category)
- emar(subject_id, hadm_id, emar_id, charttime, medication, event_txt) — covers 65/100 patients only
- microbiologyevents(microevent_id, subject_id, hadm_id, charttime, chartdate, spec_type_desc, test_name, org_name, ...)
- procedures_icd(subject_id, hadm_id, seq_num, chartdate, icd_code, icd_version) + d_icd_procedures
- diagnoses_icd / drgcodes — billing context only (no event timestamps on the clinical timeline)
- icustays(subject_id, hadm_id, stay_id, first_careunit, last_careunit, intime, outtime, los)
- chartevents(subject_id, hadm_id, stay_id, charttime, itemid, value, valuenum, valueuom) + d_items
- procedureevents(subject_id, hadm_id, stay_id, starttime, endtime, itemid, ...)
Timestamps are deidentified (date-shifted into 2110–2210).
""".strip()
