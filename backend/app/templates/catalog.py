"""Curated Query Template catalog (~14). LLM chooses a template; SQL runs locally."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import duckdb

from app.db import fetchall_dicts
from app.models import Provenance
from app.services.coverage import coverage_for_table


@dataclass
class TemplateResult:
    rows: list[dict[str, Any]]
    provenance: list[Provenance]
    sql: str
    coverage_table: str


@dataclass
class TemplateDef:
    id: str
    name: str
    description: str
    slots: list[str]
    example_question: str
    coverage_table: str
    runner: Callable[..., TemplateResult]
    example_slots: dict[str, Any] = field(default_factory=dict)


def _prov(table: str, field: str, row_id: Any, time: Any = None) -> Provenance:
    return Provenance(
        table=table,
        field=field,
        row_id=row_id if row_id is not None else None,
        time=str(time) if time is not None else None,
    )


def _bind_context(slots: dict[str, Any], subject_id: int, hadm_id: int | None) -> dict[str, Any]:
    bound = dict(slots)
    bound["subject_id"] = subject_id
    if hadm_id is not None:
        bound.setdefault("hadm_id", hadm_id)
    return bound


def run_labs_by_window(
    con: duckdb.DuckDBPyConnection, subject_id: int, hadm_id: int | None, slots: dict[str, Any]
) -> TemplateResult:
    bound = _bind_context(slots, subject_id, hadm_id)
    if "hadm_id" not in bound:
        raise ValueError("hadm_id required")
    sql = """
    SELECT l.labevent_id, CAST(l.charttime AS VARCHAR) AS charttime,
           d.label, l.value, l.valuenum, l.valueuom, l.flag
    FROM labevents l
    LEFT JOIN d_labitems d ON l.itemid = d.itemid
    WHERE l.subject_id = ? AND l.hadm_id = ?
      AND (? IS NULL OR l.charttime >= CAST(? AS TIMESTAMP))
      AND (? IS NULL OR l.charttime <= CAST(? AS TIMESTAMP))
    ORDER BY l.charttime
    LIMIT 500
    """
    start = bound.get("start")
    end = bound.get("end")
    params = [bound["subject_id"], bound["hadm_id"], start, start, end, end]
    rows = fetchall_dicts(con, sql, params)
    prov = [_prov("labevents", "valuenum", r["labevent_id"], r["charttime"]) for r in rows]
    return TemplateResult(rows=rows, provenance=prov, sql=sql.strip(), coverage_table="labevents")


def run_lab_trend(
    con: duckdb.DuckDBPyConnection, subject_id: int, hadm_id: int | None, slots: dict[str, Any]
) -> TemplateResult:
    bound = _bind_context(slots, subject_id, hadm_id)
    label = bound.get("lab_label")
    if not label:
        raise ValueError("lab_label required")
    sql = """
    SELECT l.labevent_id, CAST(l.charttime AS VARCHAR) AS charttime,
           d.label, l.valuenum, l.valueuom, l.flag
    FROM labevents l
    JOIN d_labitems d ON l.itemid = d.itemid
    WHERE l.subject_id = ?
      AND (? IS NULL OR l.hadm_id = ?)
      AND lower(d.label) LIKE lower(?)
    ORDER BY l.charttime
    LIMIT 500
    """
    pattern = f"%{label}%"
    params = [bound["subject_id"], bound.get("hadm_id"), bound.get("hadm_id"), pattern]
    rows = fetchall_dicts(con, sql, params)
    prov = [_prov("labevents", "valuenum", r["labevent_id"], r["charttime"]) for r in rows]
    return TemplateResult(rows=rows, provenance=prov, sql=sql.strip(), coverage_table="labevents")


def run_med_admins(
    con: duckdb.DuckDBPyConnection, subject_id: int, hadm_id: int | None, slots: dict[str, Any]
) -> TemplateResult:
    bound = _bind_context(slots, subject_id, hadm_id)
    sql = """
    SELECT emar_id, CAST(charttime AS VARCHAR) AS charttime, medication, event_txt
    FROM emar
    WHERE subject_id = ?
      AND (? IS NULL OR hadm_id = ?)
      AND (? IS NULL OR lower(medication) LIKE lower(?))
    ORDER BY charttime
    LIMIT 500
    """
    med = bound.get("medication")
    med_pat = f"%{med}%" if med else None
    params = [
        bound["subject_id"],
        bound.get("hadm_id"),
        bound.get("hadm_id"),
        med_pat,
        med_pat,
    ]
    rows = fetchall_dicts(con, sql, params)
    prov = [_prov("emar", "medication", r["emar_id"], r["charttime"]) for r in rows]
    return TemplateResult(rows=rows, provenance=prov, sql=sql.strip(), coverage_table="emar")


def run_med_lookup(
    con: duckdb.DuckDBPyConnection, subject_id: int, hadm_id: int | None, slots: dict[str, Any]
) -> TemplateResult:
    # Same source as med admins; distinct intent for interpreter routing.
    return run_med_admins(con, subject_id, hadm_id, slots)


def run_transfers(
    con: duckdb.DuckDBPyConnection, subject_id: int, hadm_id: int | None, slots: dict[str, Any]
) -> TemplateResult:
    bound = _bind_context(slots, subject_id, hadm_id)
    sql = """
    SELECT transfer_id, eventtype, careunit,
           CAST(intime AS VARCHAR) AS intime, CAST(outtime AS VARCHAR) AS outtime
    FROM transfers
    WHERE subject_id = ? AND (? IS NULL OR hadm_id = ?)
    ORDER BY intime
    """
    params = [bound["subject_id"], bound.get("hadm_id"), bound.get("hadm_id")]
    rows = fetchall_dicts(con, sql, params)
    prov = [_prov("transfers", "intime", r["transfer_id"], r["intime"]) for r in rows]
    return TemplateResult(rows=rows, provenance=prov, sql=sql.strip(), coverage_table="transfers")


def run_icu_stay(
    con: duckdb.DuckDBPyConnection, subject_id: int, hadm_id: int | None, slots: dict[str, Any]
) -> TemplateResult:
    bound = _bind_context(slots, subject_id, hadm_id)
    sql = """
    SELECT stay_id, first_careunit, last_careunit,
           CAST(intime AS VARCHAR) AS intime, CAST(outtime AS VARCHAR) AS outtime, los
    FROM icustays
    WHERE subject_id = ? AND (? IS NULL OR hadm_id = ?)
    ORDER BY intime
    """
    params = [bound["subject_id"], bound.get("hadm_id"), bound.get("hadm_id")]
    rows = fetchall_dicts(con, sql, params)
    prov = [_prov("icustays", "intime", r["stay_id"], r["intime"]) for r in rows]
    return TemplateResult(rows=rows, provenance=prov, sql=sql.strip(), coverage_table="icustays")


def run_procedures(
    con: duckdb.DuckDBPyConnection, subject_id: int, hadm_id: int | None, slots: dict[str, Any]
) -> TemplateResult:
    """Hospital ICD procedures and ICU procedure events (Timeline Event taxonomy)."""
    bound = _bind_context(slots, subject_id, hadm_id)
    params = [bound["subject_id"], bound.get("hadm_id"), bound.get("hadm_id")]
    hosp_sql = """
    SELECT p.hadm_id, p.seq_num, CAST(p.chartdate AS VARCHAR) AS event_time,
           p.icd_code, d.long_title
    FROM procedures_icd p
    LEFT JOIN d_icd_procedures d
      ON p.icd_code = d.icd_code AND p.icd_version = d.icd_version
    WHERE p.subject_id = ? AND (? IS NULL OR p.hadm_id = ?)
    ORDER BY p.chartdate, p.seq_num
    """
    icu_sql = """
    SELECT pe.hadm_id, pe.orderid, pe.stay_id,
           CAST(pe.starttime AS VARCHAR) AS event_time,
           CAST(pe.endtime AS VARCHAR) AS end_time,
           d.label
    FROM procedureevents pe
    LEFT JOIN d_items d ON pe.itemid = d.itemid
    WHERE pe.subject_id = ? AND (? IS NULL OR pe.hadm_id = ?)
    ORDER BY pe.starttime
    """
    paired: list[tuple[dict[str, Any], Provenance]] = []
    for r in fetchall_dicts(con, hosp_sql, params):
        row = {
            "source": "procedures_icd",
            "hadm_id": r["hadm_id"],
            "event_time": r["event_time"],
            "label": r["long_title"] or f"Procedure {r['icd_code']}",
            "detail": r["icd_code"],
            "seq_num": r["seq_num"],
        }
        paired.append(
            (
                row,
                _prov(
                    "procedures_icd",
                    "icd_code",
                    f"{r['hadm_id']}:{r['seq_num']}",
                    r["event_time"],
                ),
            )
        )
    for r in fetchall_dicts(con, icu_sql, params):
        orderid = int(r["orderid"]) if r["orderid"] is not None else None
        row = {
            "source": "procedureevents",
            "hadm_id": r["hadm_id"],
            "event_time": r["event_time"],
            "end_time": r["end_time"],
            "label": r["label"] or "ICU procedure",
            "stay_id": int(r["stay_id"]) if r["stay_id"] is not None else None,
            "orderid": orderid,
        }
        paired.append(
            (
                row,
                _prov("procedureevents", "starttime", orderid, r["event_time"]),
            )
        )
    paired.sort(key=lambda item: (item[0].get("event_time") or "", item[0]["source"]))
    rows = [item[0] for item in paired]
    prov = [item[1] for item in paired]
    sql = f"-- procedures: union hosp ICD + ICU procedureevents\n{hosp_sql.strip()}\n-- UNION\n{icu_sql.strip()}"
    return TemplateResult(rows=rows, provenance=prov, sql=sql, coverage_table="procedures_icd")


def run_microbiology(
    con: duckdb.DuckDBPyConnection, subject_id: int, hadm_id: int | None, slots: dict[str, Any]
) -> TemplateResult:
    bound = _bind_context(slots, subject_id, hadm_id)
    sql = """
    SELECT microevent_id,
           CAST(COALESCE(charttime, chartdate) AS VARCHAR) AS event_time,
           spec_type_desc, test_name, org_name, interpretation
    FROM microbiologyevents
    WHERE subject_id = ? AND (? IS NULL OR hadm_id = ?)
    ORDER BY event_time
    LIMIT 500
    """
    params = [bound["subject_id"], bound.get("hadm_id"), bound.get("hadm_id")]
    rows = fetchall_dicts(con, sql, params)
    prov = [_prov("microbiologyevents", "org_name", r["microevent_id"], r["event_time"]) for r in rows]
    return TemplateResult(rows=rows, provenance=prov, sql=sql.strip(), coverage_table="microbiologyevents")


def run_vitals_summary(
    con: duckdb.DuckDBPyConnection, subject_id: int, hadm_id: int | None, slots: dict[str, Any]
) -> TemplateResult:
    bound = _bind_context(slots, subject_id, hadm_id)
    sql = """
    SELECT c.stay_id, c.itemid, CAST(c.charttime AS VARCHAR) AS charttime,
           c.valuenum, c.valueuom, d.label
    FROM chartevents c
    JOIN d_items d ON c.itemid = d.itemid
    WHERE c.subject_id = ? AND (? IS NULL OR c.hadm_id = ?)
      AND d.label IN (
        'Heart Rate', 'Respiratory Rate', 'O2 saturation pulseoxymetry',
        'Non Invasive Blood Pressure systolic', 'Non Invasive Blood Pressure diastolic'
      )
      AND c.valuenum IS NOT NULL
      AND (? IS NULL OR c.charttime >= CAST(? AS TIMESTAMP))
      AND (? IS NULL OR c.charttime <= CAST(? AS TIMESTAMP))
    ORDER BY c.charttime, d.label
    """
    start = bound.get("start")
    end = bound.get("end")
    params = [
        bound["subject_id"],
        bound.get("hadm_id"),
        bound.get("hadm_id"),
        start,
        start,
        end,
        end,
    ]
    detail = fetchall_dicts(con, sql, params)
    if not detail:
        return TemplateResult(rows=[], provenance=[], sql=sql.strip(), coverage_table="chartevents")

    by_label: dict[str, list[dict[str, Any]]] = {}
    for r in detail:
        by_label.setdefault(r["label"], []).append(r)

    summary: list[dict[str, Any]] = []
    for label in sorted(by_label):
        vals = [float(r["valuenum"]) for r in by_label[label]]
        times = [r["charttime"] for r in by_label[label]]
        summary.append(
            {
                "role": "summary",
                "label": label,
                "n": len(vals),
                "min_val": min(vals),
                "max_val": max(vals),
                "avg_val": sum(vals) / len(vals),
                "first_time": min(times),
                "last_time": max(times),
            }
        )

    out_rows = summary + [{"role": "contributor", **r} for r in detail]
    prov = [
        _prov(
            "chartevents",
            "valuenum",
            f"{r['stay_id']}:{r['itemid']}:{r['charttime']}",
            r["charttime"],
        )
        for r in detail
    ]
    return TemplateResult(rows=out_rows, provenance=prov, sql=sql.strip(), coverage_table="chartevents")


def run_first_last(
    con: duckdb.DuckDBPyConnection, subject_id: int, hadm_id: int | None, slots: dict[str, Any]
) -> TemplateResult:
    bound = _bind_context(slots, subject_id, hadm_id)
    which = (bound.get("which") or "first").lower()
    event_kind = (bound.get("event_kind") or "lab").lower()
    order = "ASC" if which == "first" else "DESC"
    if event_kind == "lab":
        label = bound.get("lab_label") or ""
        sql = f"""
        SELECT l.labevent_id, CAST(l.charttime AS VARCHAR) AS charttime,
               d.label, l.valuenum, l.valueuom
        FROM labevents l
        JOIN d_labitems d ON l.itemid = d.itemid
        WHERE l.subject_id = ? AND (? IS NULL OR l.hadm_id = ?)
          AND (? = '' OR lower(d.label) LIKE lower(?))
        ORDER BY l.charttime {order}
        LIMIT 1
        """
        pat = f"%{label}%" if label else ""
        params = [bound["subject_id"], bound.get("hadm_id"), bound.get("hadm_id"), label, pat]
        rows = fetchall_dicts(con, sql, params)
        prov = [_prov("labevents", "valuenum", r["labevent_id"], r["charttime"]) for r in rows]
        return TemplateResult(rows=rows, provenance=prov, sql=sql.strip(), coverage_table="labevents")
    if event_kind == "medication":
        sql = f"""
        SELECT emar_id, CAST(charttime AS VARCHAR) AS charttime, medication, event_txt
        FROM emar
        WHERE subject_id = ? AND (? IS NULL OR hadm_id = ?)
        ORDER BY charttime {order}
        LIMIT 1
        """
        params = [bound["subject_id"], bound.get("hadm_id"), bound.get("hadm_id")]
        rows = fetchall_dicts(con, sql, params)
        prov = [_prov("emar", "medication", r["emar_id"], r["charttime"]) for r in rows]
        return TemplateResult(rows=rows, provenance=prov, sql=sql.strip(), coverage_table="emar")
    # transfer default
    sql = f"""
    SELECT transfer_id, eventtype, careunit, CAST(intime AS VARCHAR) AS intime
    FROM transfers
    WHERE subject_id = ? AND (? IS NULL OR hadm_id = ?)
    ORDER BY intime {order}
    LIMIT 1
    """
    params = [bound["subject_id"], bound.get("hadm_id"), bound.get("hadm_id")]
    rows = fetchall_dicts(con, sql, params)
    prov = [_prov("transfers", "intime", r["transfer_id"], r["intime"]) for r in rows]
    return TemplateResult(rows=rows, provenance=prov, sql=sql.strip(), coverage_table="transfers")


def run_events_between(
    con: duckdb.DuckDBPyConnection, subject_id: int, hadm_id: int | None, slots: dict[str, Any]
) -> TemplateResult:
    bound = _bind_context(slots, subject_id, hadm_id)
    start = bound.get("start")
    end = bound.get("end")
    if not start or not end:
        raise ValueError("start and end required")
    sql = """
    SELECT 'lab' AS event_type, CAST(charttime AS VARCHAR) AS event_time,
           CAST(labevent_id AS VARCHAR) AS row_id, CAST(itemid AS VARCHAR) AS label
    FROM labevents
    WHERE subject_id = ? AND (? IS NULL OR hadm_id = ?)
      AND charttime >= CAST(? AS TIMESTAMP) AND charttime <= CAST(? AS TIMESTAMP)
    UNION ALL
    SELECT 'medication', CAST(charttime AS VARCHAR), CAST(emar_id AS VARCHAR), medication
    FROM emar
    WHERE subject_id = ? AND (? IS NULL OR hadm_id = ?)
      AND charttime >= CAST(? AS TIMESTAMP) AND charttime <= CAST(? AS TIMESTAMP)
    UNION ALL
    SELECT 'transfer', CAST(intime AS VARCHAR), CAST(transfer_id AS VARCHAR), careunit
    FROM transfers
    WHERE subject_id = ? AND (? IS NULL OR hadm_id = ?)
      AND intime >= CAST(? AS TIMESTAMP) AND intime <= CAST(? AS TIMESTAMP)
    ORDER BY event_time
    LIMIT 500
    """
    hid = bound.get("hadm_id")
    params = [
        bound["subject_id"], hid, hid, start, end,
        bound["subject_id"], hid, hid, start, end,
        bound["subject_id"], hid, hid, start, end,
    ]
    rows = fetchall_dicts(con, sql, params)
    table_map = {"lab": "labevents", "medication": "emar", "transfer": "transfers"}
    prov = [
        _prov(table_map.get(r["event_type"], "labevents"), "event_time", r["row_id"], r["event_time"])
        for r in rows
    ]
    return TemplateResult(rows=rows, provenance=prov, sql=sql.strip(), coverage_table="labevents")


def run_event_ordering(
    con: duckdb.DuckDBPyConnection, subject_id: int, hadm_id: int | None, slots: dict[str, Any]
) -> TemplateResult:
    """Compare timestamps of two labeled events (A before B?)."""
    bound = _bind_context(slots, subject_id, hadm_id)
    a_label = bound.get("event_a")
    b_label = bound.get("event_b")
    if not a_label or not b_label:
        raise ValueError("event_a and event_b required")

    def first_lab(label: str) -> dict[str, Any] | None:
        rows = fetchall_dicts(
            con,
            """
            SELECT l.labevent_id AS row_id, CAST(l.charttime AS VARCHAR) AS event_time,
                   d.label, 'labevents' AS src
            FROM labevents l JOIN d_labitems d ON l.itemid = d.itemid
            WHERE l.subject_id = ? AND (? IS NULL OR l.hadm_id = ?)
              AND lower(d.label) LIKE lower(?)
            ORDER BY l.charttime LIMIT 1
            """,
            [bound["subject_id"], bound.get("hadm_id"), bound.get("hadm_id"), f"%{label}%"],
        )
        return rows[0] if rows else None

    def first_med(label: str) -> dict[str, Any] | None:
        rows = fetchall_dicts(
            con,
            """
            SELECT emar_id AS row_id, CAST(charttime AS VARCHAR) AS event_time,
                   medication AS label, 'emar' AS src
            FROM emar
            WHERE subject_id = ? AND (? IS NULL OR hadm_id = ?)
              AND lower(medication) LIKE lower(?)
            ORDER BY charttime LIMIT 1
            """,
            [bound["subject_id"], bound.get("hadm_id"), bound.get("hadm_id"), f"%{label}%"],
        )
        return rows[0] if rows else None

    a = first_lab(a_label) or first_med(a_label)
    b = first_lab(b_label) or first_med(b_label)
    rows: list[dict[str, Any]] = []
    if a:
        rows.append({"role": "event_a", **a})
    if b:
        rows.append({"role": "event_b", **b})
    if a and b:
        rows.append(
            {
                "role": "ordering",
                "a_before_b": a["event_time"] < b["event_time"],
                "a_time": a["event_time"],
                "b_time": b["event_time"],
            }
        )
    prov = [
        _prov(r["src"], "event_time", r["row_id"], r["event_time"])
        for r in rows
        if r.get("role") in ("event_a", "event_b")
    ]
    sql = "-- event_ordering: first matching lab/med timestamps for event_a vs event_b"
    return TemplateResult(rows=rows, provenance=prov, sql=sql, coverage_table="labevents")


def run_counts(
    con: duckdb.DuckDBPyConnection, subject_id: int, hadm_id: int | None, slots: dict[str, Any]
) -> TemplateResult:
    bound = _bind_context(slots, subject_id, hadm_id)
    target = (bound.get("count_target") or "transfers").lower()
    table_sql = {
        "transfers": (
            "SELECT transfer_id AS row_id, CAST(intime AS VARCHAR) AS event_time, careunit AS label FROM transfers WHERE subject_id = ? AND (? IS NULL OR hadm_id = ?)",
            "transfers",
            "intime",
        ),
        "labs": (
            "SELECT labevent_id AS row_id, CAST(charttime AS VARCHAR) AS event_time, CAST(itemid AS VARCHAR) AS label FROM labevents WHERE subject_id = ? AND (? IS NULL OR hadm_id = ?)",
            "labevents",
            "charttime",
        ),
        "medications": (
            "SELECT emar_id AS row_id, CAST(charttime AS VARCHAR) AS event_time, medication AS label FROM emar WHERE subject_id = ? AND (? IS NULL OR hadm_id = ?)",
            "emar",
            "charttime",
        ),
        "procedures": (
            "SELECT seq_num AS row_id, CAST(chartdate AS VARCHAR) AS event_time, icd_code AS label FROM procedures_icd WHERE subject_id = ? AND (? IS NULL OR hadm_id = ?)",
            "procedures_icd",
            "chartdate",
        ),
        "icu_stays": (
            "SELECT stay_id AS row_id, CAST(intime AS VARCHAR) AS event_time, first_careunit AS label FROM icustays WHERE subject_id = ? AND (? IS NULL OR hadm_id = ?)",
            "icustays",
            "intime",
        ),
    }
    if target not in table_sql:
        raise ValueError(f"Unsupported count_target: {target}")
    detail_sql, table, time_field = table_sql[target]
    rows = fetchall_dicts(con, detail_sql, [bound["subject_id"], bound.get("hadm_id"), bound.get("hadm_id")])
    summary = [{"count_target": target, "count": len(rows)}]
    out_rows = summary + [{"role": "contributor", **r} for r in rows]
    prov = [_prov(table, time_field, r["row_id"], r["event_time"]) for r in rows]
    return TemplateResult(rows=out_rows, provenance=prov, sql=detail_sql, coverage_table=table)


def run_admission_overview(
    con: duckdb.DuckDBPyConnection, subject_id: int, hadm_id: int | None, slots: dict[str, Any]
) -> TemplateResult:
    bound = _bind_context(slots, subject_id, hadm_id)
    if "hadm_id" not in bound or bound["hadm_id"] is None:
        raise ValueError("hadm_id required")
    sql = """
    SELECT a.hadm_id,
           CAST(a.admittime AS VARCHAR) AS admittime,
           CAST(a.dischtime AS VARCHAR) AS dischtime,
           a.admission_type, a.admission_location, a.discharge_location,
           a.hospital_expire_flag,
           (SELECT COUNT(*) FROM transfers t WHERE t.hadm_id = a.hadm_id) AS transfer_count,
           (SELECT COUNT(*) FROM labevents l WHERE l.hadm_id = a.hadm_id) AS lab_count,
           (SELECT COUNT(*) FROM emar e WHERE e.hadm_id = a.hadm_id) AS emar_count,
           (SELECT COUNT(*) FROM icustays i WHERE i.hadm_id = a.hadm_id) AS icu_stay_count
    FROM admissions a
    WHERE a.subject_id = ? AND a.hadm_id = ?
    """
    rows = fetchall_dicts(con, sql, [bound["subject_id"], bound["hadm_id"]])
    prov = [_prov("admissions", "admittime", r["hadm_id"], r["admittime"]) for r in rows]
    return TemplateResult(rows=rows, provenance=prov, sql=sql.strip(), coverage_table="admissions")


CATALOG: list[TemplateDef] = [
    TemplateDef(
        id="labs_by_window",
        name="Labs by admission/window",
        description="List laboratory results for an Admission, optionally within a time window.",
        slots=["hadm_id", "start", "end"],
        example_question="What labs were recorded during this admission?",
        coverage_table="labevents",
        runner=run_labs_by_window,
    ),
    TemplateDef(
        id="lab_trend",
        name="Lab trend for one item",
        description="Time series for a named lab (e.g. Creatinine, Potassium) for a Patient/Admission.",
        slots=["lab_label", "hadm_id"],
        example_question="Show the creatinine trend for this patient.",
        coverage_table="labevents",
        runner=run_lab_trend,
        example_slots={"lab_label": "Creatinine"},
    ),
    TemplateDef(
        id="med_admins",
        name="Medication administrations",
        description="eMAR medication administrations for a Patient/Admission; optional medication name filter.",
        slots=["hadm_id", "medication"],
        example_question="Which medications were administered during this admission?",
        coverage_table="emar",
        runner=run_med_admins,
    ),
    TemplateDef(
        id="med_lookup",
        name="Medication lookup",
        description="Look up whether a named medication appears in eMAR for this Patient/Admission.",
        slots=["medication", "hadm_id"],
        example_question="Was heparin administered?",
        coverage_table="emar",
        runner=run_med_lookup,
        example_slots={"medication": "Heparin"},
    ),
    TemplateDef(
        id="transfers",
        name="Transfers / locations",
        description="Ward and care-unit transfers for a Patient/Admission.",
        slots=["hadm_id"],
        example_question="Where was the patient transferred during this admission?",
        coverage_table="transfers",
        runner=run_transfers,
    ),
    TemplateDef(
        id="icu_stay",
        name="ICU stay details",
        description="ICU Stay intervals (stay_id, care units, LOS) for a Patient/Admission.",
        slots=["hadm_id"],
        example_question="What ICU stays occurred during this admission?",
        coverage_table="icustays",
        runner=run_icu_stay,
    ),
    TemplateDef(
        id="procedures",
        name="Procedures",
        description=(
            "Hospital ICD procedures and ICU procedure events for a Patient/Admission "
            "(union matching the Timeline Event taxonomy)."
        ),
        slots=["hadm_id"],
        example_question="What procedures were coded for this admission?",
        coverage_table="procedures_icd",
        runner=run_procedures,
    ),
    TemplateDef(
        id="microbiology",
        name="Microbiology",
        description="Microbiology specimens, tests, and organisms for a Patient/Admission.",
        slots=["hadm_id"],
        example_question="What microbiology results are in the record?",
        coverage_table="microbiologyevents",
        runner=run_microbiology,
    ),
    TemplateDef(
        id="vitals_summary",
        name="Vitals summary for a window",
        description="Aggregate summary of common ICU vital signs for a window.",
        slots=["hadm_id", "start", "end"],
        example_question="Summarize heart rate and respiratory rate for this admission.",
        coverage_table="chartevents",
        runner=run_vitals_summary,
    ),
    TemplateDef(
        id="first_last",
        name="First/last occurrence",
        description="First or last occurrence of a lab, medication, or transfer.",
        slots=["which", "event_kind", "lab_label", "hadm_id"],
        example_question="When was the first potassium lab?",
        coverage_table="labevents",
        runner=run_first_last,
        example_slots={"which": "first", "event_kind": "lab", "lab_label": "Potassium"},
    ),
    TemplateDef(
        id="events_between",
        name="Events between two times",
        description="Labs, medications, and transfers between two timestamps.",
        slots=["start", "end", "hadm_id"],
        example_question="What events happened between admit and the first ICU transfer?",
        coverage_table="labevents",
        runner=run_events_between,
    ),
    TemplateDef(
        id="event_ordering",
        name="Event ordering",
        description="Did event A happen before event B? Returns both timestamps and Provenance.",
        slots=["event_a", "event_b", "hadm_id"],
        example_question="Did the first creatinine lab happen before the first heparin administration?",
        coverage_table="labevents",
        runner=run_event_ordering,
        example_slots={"event_a": "Creatinine", "event_b": "Heparin"},
    ),
    TemplateDef(
        id="counts",
        name="Counts / aggregates",
        description="Count transfers, labs, medications, procedures, or ICU stays, with contributing rows.",
        slots=["count_target", "hadm_id"],
        example_question="How many transfers occurred during this admission?",
        coverage_table="transfers",
        runner=run_counts,
        example_slots={"count_target": "transfers"},
    ),
    TemplateDef(
        id="admission_overview",
        name="Admission overview",
        description="High-level Admission facts and event counts.",
        slots=["hadm_id"],
        example_question="Give an overview of this admission.",
        coverage_table="admissions",
        runner=run_admission_overview,
    ),
]

TEMPLATE_BY_ID = {t.id: t for t in CATALOG}


def catalog_for_llm() -> list[dict[str, Any]]:
    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "slots": t.slots,
            "example_question": t.example_question,
        }
        for t in CATALOG
    ]


def run_template(
    con: duckdb.DuckDBPyConnection,
    template_id: str,
    subject_id: int,
    hadm_id: int | None,
    slots: dict[str, Any],
) -> TemplateResult:
    tmpl = TEMPLATE_BY_ID.get(template_id)
    if not tmpl:
        raise KeyError(f"Unknown template: {template_id}")
    return tmpl.runner(con, subject_id, hadm_id, slots)


def example_questions() -> list[dict[str, str]]:
    return [
        {
            "question": t.example_question,
            "template_id": t.id,
            "description": t.description,
        }
        for t in CATALOG
    ]
