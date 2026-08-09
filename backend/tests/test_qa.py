from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.interpreters.base import Abstain, InterpretResult, TemplateChoice
from app.interpreters.fake import FakeInterpreter
from app.interpreters.keyword import KeywordBaselineInterpreter
from app.main import create_app


class _ScriptedInterpreter:
    """Test double: fixed name + scripted interpret results or raised errors."""

    def __init__(
        self,
        name: str,
        result: InterpretResult | None = None,
        *,
        error: Exception | None = None,
    ) -> None:
        self.name = name
        self._result = result
        self._error = error

    def interpret(
        self,
        question: str,
        schema: str,
        catalog: list[dict[str, Any]],
    ) -> InterpretResult:
        if self._error is not None:
            raise self._error
        assert self._result is not None
        return self._result


def _client_with(interpreter: Any, *, raise_server_exceptions: bool = True) -> TestClient:
    app = create_app()
    app.state.interpreter = interpreter
    return TestClient(app, raise_server_exceptions=raise_server_exceptions)


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


def test_llm_no_template_abstain_never_reroutes_to_keyword(client: TestClient) -> None:
    """Hard-cut: LLM Abstain(no_template) stays abstention even when keyword could answer."""
    sid, hadm = _patient_with_emar(client)
    question = "How many transfers during this admission?"
    # Keyword baseline would choose counts; LLM abstains — must not silently keyword.
    interp = _ScriptedInterpreter(
        "llm",
        Abstain(reason="No Query Template fits this question.", trigger="no_template"),
    )
    with _client_with(interp) as c:
        res = c.post(
            "/qa",
            json={"question": question, "subject_id": sid, "hadm_id": hadm},
        )
    assert res.status_code == 200
    body = res.json()
    assert body["kind"] == "abstention"
    assert body["interpreter"] == "llm"
    assert body["rows"] == []
    assert body["template_id"] is None


def test_llm_clinical_advice_abstain_never_reroutes_to_keyword(client: TestClient) -> None:
    sid, hadm = _patient_with_emar(client)
    interp = _ScriptedInterpreter(
        "llm",
        Abstain(
            reason="Out of scope: Chronicle does not provide clinical advice.",
            trigger="clinical_advice",
        ),
    )
    with _client_with(interp) as c:
        res = c.post(
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
    assert body["interpreter"] == "llm"
    assert body["rows"] == []


def test_llm_transport_failure_uses_keyword_rescue(client: TestClient) -> None:
    sid, hadm = _patient_with_emar(client)
    interp = _ScriptedInterpreter("llm", error=RuntimeError("LLM API unreachable"))
    with _client_with(interp) as c:
        res = c.post(
            "/qa",
            json={
                "question": "How many transfers during this admission?",
                "subject_id": sid,
                "hadm_id": hadm,
            },
        )
    assert res.status_code == 200
    body = res.json()
    assert body["kind"] in ("grounded", "no_data")
    assert body["interpreter"] == "keyword_rescue"
    assert body["template_id"] == "counts"


def test_fake_primary_transport_failure_does_not_rescue(client: TestClient) -> None:
    sid, hadm = _patient_with_emar(client)
    interp = _ScriptedInterpreter("fake", error=RuntimeError("fake boom"))
    with _client_with(interp, raise_server_exceptions=False) as c:
        res = c.post(
            "/qa",
            json={
                "question": "How many transfers during this admission?",
                "subject_id": sid,
                "hadm_id": hadm,
            },
        )
    assert res.status_code == 500
    assert "keyword_rescue" not in res.text
    assert '"kind":"grounded"' not in res.text.replace(" ", "")


def test_keyword_primary_transport_failure_does_not_rescue(client: TestClient) -> None:
    sid, hadm = _patient_with_emar(client)
    interp = _ScriptedInterpreter("keyword", error=RuntimeError("keyword boom"))
    with _client_with(interp, raise_server_exceptions=False) as c:
        res = c.post(
            "/qa",
            json={
                "question": "How many transfers during this admission?",
                "subject_id": sid,
                "hadm_id": hadm,
            },
        )
    assert res.status_code == 500
    assert "keyword_rescue" not in res.text


def test_bad_slots_return_http_400_not_abstention(client: TestClient) -> None:
    sid, hadm = _patient_with_emar(client)
    interp = _ScriptedInterpreter(
        "fake",
        TemplateChoice(template_id="lab_trend", slots={}),
    )
    with _client_with(interp) as c:
        res = c.post(
            "/qa",
            json={
                "question": "Show lab trend without label",
                "subject_id": sid,
                "hadm_id": hadm,
            },
        )
    assert res.status_code == 400
    body = res.json()
    assert "detail" in body
    assert body.get("kind") != "abstention"


def test_unknown_template_execution_returns_http_400(client: TestClient) -> None:
    sid, hadm = _patient_with_emar(client)
    interp = _ScriptedInterpreter(
        "fake",
        TemplateChoice(template_id="not_a_real_template", slots={}),
    )
    with _client_with(interp) as c:
        res = c.post(
            "/qa",
            json={
                "question": "Force unknown template",
                "subject_id": sid,
                "hadm_id": hadm,
            },
        )
    assert res.status_code == 400
    body = res.json()
    assert "detail" in body
    assert body.get("kind") != "abstention"


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
    body = res.json()
    assert len(body) >= 10
    ids = {e["template_id"] for e in body}
    required = {
        "labs_by_window",
        "lab_trend",
        "med_admins",
        "med_lookup",
        "transfers",
        "icu_stay",
        "procedures",
        "microbiology",
        "vitals_summary",
        "first_last",
        "events_between",
        "event_ordering",
        "counts",
        "admission_overview",
    }
    assert required.issubset(ids)


def test_health(client: TestClient) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["patient_count"] == 100
    assert "schema" in body["egress_note"].lower() or "Patient rows never" in body["egress_note"]
