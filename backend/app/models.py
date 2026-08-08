from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class Provenance(BaseModel):
    table: str
    field: str
    row_id: str | int | None
    time: str | None = None


class TableCoverage(BaseModel):
    table: str
    has_rows: bool
    row_count: int
    note: str | None = None


class PatientSummary(BaseModel):
    subject_id: int
    gender: str | None
    anchor_age: int | None
    anchor_year_group: str | None
    dod: str | None = None
    admission_count: int
    coverage: list[TableCoverage]


class AdmissionChapter(BaseModel):
    hadm_id: int
    admittime: str | None
    dischtime: str | None
    admission_type: str | None
    admission_location: str | None
    discharge_location: str | None
    hospital_expire_flag: int | None
    icu_stay_count: int


class PatientDetail(BaseModel):
    subject_id: int
    gender: str | None
    anchor_age: int | None
    anchor_year: int | None
    anchor_year_group: str | None
    dod: str | None = None
    coverage: list[TableCoverage]
    admissions: list[AdmissionChapter]
    date_shift_note: str = (
        "Timestamps in MIMIC-IV Demo are deidentified and date-shifted "
        "(typically into the 2110–2210 range). Ages are anchor ages; ages > 89 appear as 91."
    )


class TimelineEvent(BaseModel):
    event_type: str
    time: str | None
    end_time: str | None = None
    label: str
    detail: str | None = None
    stay_id: int | None = None
    provenance: Provenance
    # For expandable ICU observation bands
    band_key: str | None = None
    band_count: int | None = None
    band_events: list[TimelineEvent] | None = None


class IcuStayInterval(BaseModel):
    stay_id: int
    first_careunit: str | None
    last_careunit: str | None
    intime: str | None
    outtime: str | None
    los: float | None
    provenance: Provenance


class TimelineResponse(BaseModel):
    subject_id: int
    hadm_id: int
    events: list[TimelineEvent]
    icu_stays: list[IcuStayInterval]
    filters_applied: dict[str, Any]


class BillingCode(BaseModel):
    code: str
    title: str | None = None
    seq_num: int | None = None
    code_type: str
    provenance: Provenance


class BillingContext(BaseModel):
    subject_id: int
    hadm_id: int
    notice: str = (
        "Billing Context: untimed discharge coding (ICD diagnoses and DRG). "
        "These are not Timeline Events and must not be read as timed clinical events."
    )
    diagnoses: list[BillingCode]
    drg_codes: list[BillingCode]


class QaRequest(BaseModel):
    question: str = Field(min_length=1)
    subject_id: int
    hadm_id: int | None = None


class QaResponse(BaseModel):
    kind: Literal["grounded", "no_data", "abstention"]
    question: str
    subject_id: int
    hadm_id: int | None = None
    summary: str
    rows: list[dict[str, Any]] = Field(default_factory=list)
    provenance: list[Provenance] = Field(default_factory=list)
    coverage: list[TableCoverage] = Field(default_factory=list)
    template_id: str | None = None
    slots: dict[str, Any] = Field(default_factory=dict)
    sql: str | None = None
    interpreter: Literal["llm", "keyword", "keyword_fallback", "fake"]
    abstention_reason: str | None = None
    is_ai_phrasing: bool = True


class ExampleQuestion(BaseModel):
    question: str
    template_id: str
    description: str


class HealthResponse(BaseModel):
    status: str
    data_dir: str
    patient_count: int
    llm_model: str
    interpreter: str
    egress_note: str = (
        "Only schema, Query Template descriptions, and the user question leave this machine. "
        "Patient rows never egress (ADR 0001)."
    )
