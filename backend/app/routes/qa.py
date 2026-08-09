from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_db, get_qa_interpreter
from app.interpreters.base import QuestionInterpreter
from app.models import ExampleQuestion, QaRequest, QaResponse
from app.services.patients import admission_belongs, patient_exists
from app.services.qa import answer_question
from app.templates.catalog import example_questions

router = APIRouter(tags=["qa"])


@router.post("/qa", response_model=QaResponse)
def api_qa(
    body: QaRequest,
    con: duckdb.DuckDBPyConnection = Depends(get_db),
    interpreter: QuestionInterpreter = Depends(get_qa_interpreter),
) -> QaResponse:
    if not patient_exists(con, body.subject_id):
        raise HTTPException(
            status_code=400,
            detail=f"Unknown Patient subject_id={body.subject_id}",
        )
    if body.hadm_id is not None and not admission_belongs(con, body.subject_id, body.hadm_id):
        raise HTTPException(
            status_code=400,
            detail=f"Admission hadm_id={body.hadm_id} does not belong to Patient {body.subject_id}",
        )
    try:
        return answer_question(
            con,
            question=body.question,
            subject_id=body.subject_id,
            hadm_id=body.hadm_id,
            interpreter=interpreter,
            allow_keyword_rescue=True,
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/qa/examples", response_model=list[ExampleQuestion])
def api_qa_examples() -> list[ExampleQuestion]:
    return [ExampleQuestion(**e) for e in example_questions()]
