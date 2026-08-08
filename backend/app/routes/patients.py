from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from app.deps import get_db
from app.models import BillingContext, PatientDetail, PatientSummary, TimelineResponse
from app.services.patients import admission_belongs, get_patient, list_patients, patient_exists
from app.services.timeline import EVENT_TYPES, billing_context, build_timeline

router = APIRouter(tags=["patients"])


@router.get("/patients", response_model=list[PatientSummary])
def api_list_patients(con: duckdb.DuckDBPyConnection = Depends(get_db)) -> list[PatientSummary]:
    return list_patients(con)


@router.get("/patients/{subject_id}", response_model=PatientDetail)
def api_get_patient(
    subject_id: int, con: duckdb.DuckDBPyConnection = Depends(get_db)
) -> PatientDetail:
    detail = get_patient(con, subject_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Unknown Patient subject_id={subject_id}")
    return detail


@router.get(
    "/patients/{subject_id}/admissions/{hadm_id}/timeline",
    response_model=TimelineResponse,
)
def api_timeline(
    subject_id: int,
    hadm_id: int,
    event_types: str | None = Query(
        None, description="Comma-separated event types to include"
    ),
    start: str | None = None,
    end: str | None = None,
    con: duckdb.DuckDBPyConnection = Depends(get_db),
) -> TimelineResponse:
    if not patient_exists(con, subject_id):
        raise HTTPException(status_code=404, detail=f"Unknown Patient subject_id={subject_id}")
    if not admission_belongs(con, subject_id, hadm_id):
        raise HTTPException(
            status_code=404,
            detail=f"Admission hadm_id={hadm_id} not found for Patient {subject_id}",
        )
    types = None
    if event_types:
        types = {t.strip() for t in event_types.split(",") if t.strip()}
    try:
        return build_timeline(con, subject_id, hadm_id, types, start, end)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/patients/{subject_id}/admissions/{hadm_id}/billing-context",
    response_model=BillingContext,
)
def api_billing(
    subject_id: int,
    hadm_id: int,
    con: duckdb.DuckDBPyConnection = Depends(get_db),
) -> BillingContext:
    if not patient_exists(con, subject_id):
        raise HTTPException(status_code=404, detail=f"Unknown Patient subject_id={subject_id}")
    if not admission_belongs(con, subject_id, hadm_id):
        raise HTTPException(
            status_code=404,
            detail=f"Admission hadm_id={hadm_id} not found for Patient {subject_id}",
        )
    return billing_context(con, subject_id, hadm_id)


@router.get("/meta/event-types")
def api_event_types() -> list[str]:
    return sorted(EVENT_TYPES)
