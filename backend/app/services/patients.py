from __future__ import annotations

import duckdb

from app.db import fetchall_dicts, fetchone_dict
from app.models import AdmissionChapter, PatientDetail, PatientSummary
from app.services.coverage import all_patients_coverage, patient_coverage


def list_patients(con: duckdb.DuckDBPyConnection) -> list[PatientSummary]:
    rows = fetchall_dicts(
        con,
        """
        SELECT
          p.subject_id,
          p.gender,
          p.anchor_age,
          p.anchor_year_group,
          CAST(p.dod AS VARCHAR) AS dod,
          (SELECT COUNT(*) FROM admissions a WHERE a.subject_id = p.subject_id) AS admission_count
        FROM patients p
        ORDER BY p.subject_id
        """,
    )
    coverage_by_patient = all_patients_coverage(con)
    result: list[PatientSummary] = []
    for r in rows:
        sid = int(r["subject_id"])
        result.append(
            PatientSummary(
                subject_id=sid,
                gender=r["gender"],
                anchor_age=int(r["anchor_age"]) if r["anchor_age"] is not None else None,
                anchor_year_group=r["anchor_year_group"],
                dod=r["dod"],
                admission_count=int(r["admission_count"]),
                coverage=coverage_by_patient.get(sid, []),
            )
        )
    return result


def get_patient(con: duckdb.DuckDBPyConnection, subject_id: int) -> PatientDetail | None:
    p = fetchone_dict(
        con,
        """
        SELECT subject_id, gender, anchor_age, anchor_year, anchor_year_group,
               CAST(dod AS VARCHAR) AS dod
        FROM patients WHERE subject_id = ?
        """,
        [subject_id],
    )
    if not p:
        return None

    adm_rows = fetchall_dicts(
        con,
        """
        SELECT
          a.hadm_id,
          CAST(a.admittime AS VARCHAR) AS admittime,
          CAST(a.dischtime AS VARCHAR) AS dischtime,
          a.admission_type,
          a.admission_location,
          a.discharge_location,
          a.hospital_expire_flag,
          (SELECT COUNT(*) FROM icustays i WHERE i.hadm_id = a.hadm_id) AS icu_stay_count
        FROM admissions a
        WHERE a.subject_id = ?
        ORDER BY a.admittime
        """,
        [subject_id],
    )
    admissions = [
        AdmissionChapter(
            hadm_id=int(r["hadm_id"]),
            admittime=r["admittime"],
            dischtime=r["dischtime"],
            admission_type=r["admission_type"],
            admission_location=r["admission_location"],
            discharge_location=r["discharge_location"],
            hospital_expire_flag=int(r["hospital_expire_flag"])
            if r["hospital_expire_flag"] is not None
            else None,
            icu_stay_count=int(r["icu_stay_count"]),
        )
        for r in adm_rows
    ]
    return PatientDetail(
        subject_id=int(p["subject_id"]),
        gender=p["gender"],
        anchor_age=int(p["anchor_age"]) if p["anchor_age"] is not None else None,
        anchor_year=int(p["anchor_year"]) if p["anchor_year"] is not None else None,
        anchor_year_group=p["anchor_year_group"],
        dod=p["dod"],
        coverage=patient_coverage(con, subject_id),
        admissions=admissions,
    )


def patient_exists(con: duckdb.DuckDBPyConnection, subject_id: int) -> bool:
    row = fetchone_dict(con, "SELECT 1 AS ok FROM patients WHERE subject_id = ?", [subject_id])
    return row is not None


def admission_belongs(
    con: duckdb.DuckDBPyConnection, subject_id: int, hadm_id: int
) -> bool:
    row = fetchone_dict(
        con,
        "SELECT 1 AS ok FROM admissions WHERE subject_id = ? AND hadm_id = ?",
        [subject_id, hadm_id],
    )
    return row is not None
