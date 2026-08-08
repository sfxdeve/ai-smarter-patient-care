from __future__ import annotations

from fastapi.testclient import TestClient

from app.interpreters.base import Abstain, TemplateChoice
from app.interpreters.fake import FakeInterpreter
from app.interpreters.keyword import KeywordBaselineInterpreter
from app.main import create_app


def _patient_with_emar(client: TestClient) -> tuple[int, int]:
    for p in client.get("/patients").json():
        emar = next(c for c in p["coverage"] if c["table"] == "emar")
        if emar["has_rows"]:
            detail = client.get(f"/patients/{p['subject_id']}").json()
            return p["subject_id"], detail["admissions"][0]["hadm_id"]
    raise AssertionError("expected a Patient with eMAR coverage")


def _patient_without_emar(client: TestClient) -> tuple[int, int]:
    for p in client.get("/patients").json():
        emar = next(c for c in p["coverage"] if c["table"] == "emar")
        if not emar["has_rows"]:
            detail = client.get(f"/patients/{p['subject_id']}").json()
            return p["subject_id"], detail["admissions"][0]["hadm_id"]
    raise AssertionError("expected a Patient without eMAR coverage")


def test_grounded_answer_with_provenance(client: TestClient) -> None:
    sid, hadm = _patient_with_emar(client)
    res = client.post(
        "/qa",
        json={"question": "How many transfers during this admission?", "subject_id": sid, "hadm_id": hadm},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["kind"] == "grounded"
    assert body["template_id"] == "counts"
    assert body["sql"]
    assert body["provenance"]
    for p in body["provenance"]:
        assert p["table"] and p["field"] and "row_id" in p


def test_no_data_answer_includes_coverage_for_patient_without_emar(client: TestClient) -> None:
    sid, hadm = _patient_without_emar(client)
    app = create_app()
    app.state.interpreter = FakeInterpreter(
        {
            "was heparin administered?": TemplateChoice(
                template_id="med_lookup", slots={"medication": "Heparin"}
            )
        }
    )
    with TestClient(app) as c:
        res = c.post(
            "/qa",
            json={"question": "Was heparin administered?", "subject_id": sid, "hadm_id": hadm},
        )
    assert res.status_code == 200
    body = res.json()
    assert body["kind"] == "no_data"
    assert body["coverage"]
    assert body["coverage"][0]["table"] == "emar"
    assert body["coverage"][0]["has_rows"] is False
    assert "no" != body["summary"].strip().lower()
    assert "No-Data" in body["summary"] or "zero rows" in body["summary"].lower()


def test_abstention_no_template(client: TestClient) -> None:
    sid, hadm = _patient_with_emar(client)
    res = client.post(
        "/qa",
        json={"question": "What is the patient's favorite color?", "subject_id": sid, "hadm_id": hadm},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["kind"] == "abstention"
    assert body["abstention_reason"]


def test_abstention_clinical_advice(client: TestClient) -> None:
    sid, hadm = _patient_with_emar(client)
    res = client.post(
        "/qa",
        json={
            "question": "What treatment should I give this patient?",
            "subject_id": sid,
            "hadm_id": hadm,
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["kind"] == "abstention"
    assert "clinical" in body["abstention_reason"].lower() or "advice" in body["summary"].lower()


def test_unknown_patient_rejected(client: TestClient) -> None:
    res = client.post(
        "/qa",
        json={"question": "How many transfers?", "subject_id": 999999999, "hadm_id": 1},
    )
    assert res.status_code == 400


def test_keyword_baseline_behavioral() -> None:
    interp = KeywordBaselineInterpreter()
    catalog: list = []
    r = interp.interpret("How many transfers occurred?", "", catalog)
    assert isinstance(r, TemplateChoice)
    assert r.template_id == "counts"
    a = interp.interpret("Should we diagnose sepsis?", "", catalog)
    assert isinstance(a, Abstain)
    assert a.trigger == "clinical_advice"


def test_qa_examples(client: TestClient) -> None:
    res = client.get("/qa/examples")
    assert res.status_code == 200
    assert len(res.json()) >= 10


def test_health(client: TestClient) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["patient_count"] == 100
    assert "schema" in body["egress_note"].lower() or "Patient rows never" in body["egress_note"]
