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
    for p in client.get("/api/patients").json():
        emar = next(c for c in p["coverage"] if c["table"] == "emar")
        if emar["has_rows"]:
            detail = client.get(f"/api/patients/{p['subject_id']}").json()
            return p["subject_id"], detail["admissions"][0]["hadm_id"]
    raise AssertionError("expected a Patient with eMAR coverage")


def _patient_without_emar(client: TestClient) -> tuple[int, int]:
    for p in client.get("/api/patients").json():
        emar = next(c for c in p["coverage"] if c["table"] == "emar")
        if not emar["has_rows"]:
            detail = client.get(f"/api/patients/{p['subject_id']}").json()
            return p["subject_id"], detail["admissions"][0]["hadm_id"]
    raise AssertionError("expected a Patient without eMAR coverage")


def test_grounded_answer_with_provenance(client: TestClient) -> None:
    sid, hadm = _patient_with_emar(client)
    res = client.post(
        "/api/qa",
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
            "/api/qa",
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
        "/api/qa",
        json={"question": "What is the patient's favorite color?", "subject_id": sid, "hadm_id": hadm},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["kind"] == "abstention"
    assert body["abstention_reason"]


def test_abstention_clinical_advice(client: TestClient) -> None:
    sid, hadm = _patient_with_emar(client)
    res = client.post(
        "/api/qa",
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
            "/api/qa",
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
            "/api/qa",
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
            "/api/qa",
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
            "/api/qa",
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
            "/api/qa",
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
            "/api/qa",
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
            "/api/qa",
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
        "/api/qa",
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


_VITAL_LABELS = {
    "Heart Rate",
    "Respiratory Rate",
    "O2 saturation pulseoxymetry",
    "Non Invasive Blood Pressure systolic",
    "Non Invasive Blood Pressure diastolic",
}


def test_vitals_summary_grounded_with_honest_provenance() -> None:
    """In-scope vitals → grounded; every Provenance points at a real chartevents row."""
    sid, hadm = 10039708, 28258130
    question = "Summarize heart rate and respiratory rate for this admission."
    interp = _ScriptedInterpreter(
        "fake",
        TemplateChoice(template_id="vitals_summary", slots={}),
    )
    with _client_with(interp) as c:
        res = c.post(
            "/api/qa",
            json={"question": question, "subject_id": sid, "hadm_id": hadm},
        )
    assert res.status_code == 200
    body = res.json()
    assert body["kind"] == "grounded"
    assert body["template_id"] == "vitals_summary"
    assert body["provenance"], "expected non-empty provenance from source rows"
    for p in body["provenance"]:
        assert p["table"] == "chartevents"
        assert p["field"]
        assert p["row_id"] is not None
        assert p["time"]
        # Labels must not stand in as row identifiers
        assert str(p["row_id"]) not in _VITAL_LABELS
        assert ":" in str(p["row_id"]), "chartevents row_id should be composite stay_id:itemid:charttime"


def test_vitals_summary_zero_rows_is_no_data_with_chartevents_coverage() -> None:
    """Zero matching vitals window → No-Data Answer with chartevents coverage."""
    sid, hadm = 10000032, 22595853
    question = "Summarize heart rate and respiratory rate for this admission."
    interp = _ScriptedInterpreter(
        "fake",
        TemplateChoice(template_id="vitals_summary", slots={}),
    )
    with _client_with(interp) as c:
        res = c.post(
            "/api/qa",
            json={"question": question, "subject_id": sid, "hadm_id": hadm},
        )
    assert res.status_code == 200
    body = res.json()
    assert body["kind"] == "no_data"
    assert body["template_id"] == "vitals_summary"
    assert body["rows"] == []
    assert body["provenance"] == []
    assert body["coverage"]
    assert body["coverage"][0]["table"] == "chartevents"
    assert "no" != body["summary"].strip().lower()
    assert "No-Data" in body["summary"] or "zero rows" in body["summary"].lower()


def test_procedures_grounded_from_hosp_and_icu_with_honest_provenance() -> None:
    """Procedure QA returns hospital ICD and ICU procedureevents with per-source Provenance."""
    sid, hadm = 10021487, 28998349
    question = "What procedures were coded for this admission?"
    interp = _ScriptedInterpreter(
        "fake",
        TemplateChoice(template_id="procedures", slots={}),
    )
    with _client_with(interp) as c:
        res = c.post(
            "/api/qa",
            json={"question": question, "subject_id": sid, "hadm_id": hadm},
        )
    assert res.status_code == 200
    body = res.json()
    assert body["kind"] == "grounded"
    assert body["template_id"] == "procedures"
    tables = {p["table"] for p in body["provenance"]}
    assert "procedures_icd" in tables
    assert "procedureevents" in tables
    assert body["provenance"], "expected non-empty provenance from source rows"
    for p in body["provenance"]:
        assert p["table"] in ("procedures_icd", "procedureevents")
        assert p["field"]
        assert p["row_id"] is not None
        assert p["time"]
        if p["table"] == "procedures_icd":
            assert p["field"] == "icd_code"
            assert ":" in str(p["row_id"])
        else:
            assert p["field"] == "starttime"
            assert str(p["row_id"]).isdigit() or isinstance(p["row_id"], int)


def test_procedures_zero_rows_is_no_data_with_coverage() -> None:
    """Zero hospital and ICU procedures for the Admission → No-Data with coverage."""
    sid, hadm = 10002930, 28301173
    question = "What procedures were coded for this admission?"
    interp = _ScriptedInterpreter(
        "fake",
        TemplateChoice(template_id="procedures", slots={}),
    )
    with _client_with(interp) as c:
        res = c.post(
            "/api/qa",
            json={"question": question, "subject_id": sid, "hadm_id": hadm},
        )
    assert res.status_code == 200
    body = res.json()
    assert body["kind"] == "no_data"
    assert body["template_id"] == "procedures"
    assert body["rows"] == []
    assert body["provenance"] == []
    assert body["coverage"]
    assert body["coverage"][0]["table"] in ("procedures_icd", "procedureevents")
    assert "no" != body["summary"].strip().lower()
    assert "No-Data" in body["summary"] or "zero rows" in body["summary"].lower()


def test_event_ordering_zero_match_is_no_data_with_coverage() -> None:
    """Zero matches on a required side → No-Data Answer with coverage, not abstention/bare no."""
    sid, hadm = 10039708, 28258130
    question = "Did ZZZNotARealEvent happen before Creatinine?"
    interp = _ScriptedInterpreter(
        "fake",
        TemplateChoice(
            template_id="event_ordering",
            slots={"event_a": "ZZZNotARealEvent", "event_b": "Creatinine"},
        ),
    )
    with _client_with(interp) as c:
        res = c.post(
            "/api/qa",
            json={"question": question, "subject_id": sid, "hadm_id": hadm},
        )
    assert res.status_code == 200
    body = res.json()
    assert body["kind"] == "no_data"
    assert body["template_id"] == "event_ordering"
    assert body["rows"] == []
    assert body["provenance"] == []
    assert body["coverage"]
    assert body["coverage"][0]["table"]
    assert "no" != body["summary"].strip().lower()
    assert "No-Data" in body["summary"] or "zero rows" in body["summary"].lower()
    assert body.get("kind") != "abstention"


def test_event_ordering_multi_match_uses_earliest_with_dual_provenance() -> None:
    """Many Creatinine/Heparin rows → earliest each side; provenance both; summary states rule."""
    sid, hadm = 10039708, 28258130
    # Known demo earliests for this Admission (multi-match labs + eMAR).
    earliest_creatinine = "2140-01-23 19:14:00"
    earliest_heparin = "2140-01-25 18:49:00"
    question = "Did Creatinine happen before Heparin?"
    interp = _ScriptedInterpreter(
        "fake",
        TemplateChoice(
            template_id="event_ordering",
            slots={"event_a": "Creatinine", "event_b": "Heparin"},
        ),
    )
    with _client_with(interp) as c:
        res = c.post(
            "/api/qa",
            json={"question": question, "subject_id": sid, "hadm_id": hadm},
        )
    assert res.status_code == 200
    body = res.json()
    assert body["kind"] == "grounded"
    assert body["template_id"] == "event_ordering"
    by_role = {r["role"]: r for r in body["rows"] if "role" in r}
    assert by_role["event_a"]["event_time"] == earliest_creatinine
    assert by_role["event_b"]["event_time"] == earliest_heparin
    assert by_role["ordering"]["a_before_b"] is True
    assert len(body["provenance"]) >= 2
    tables = {p["table"] for p in body["provenance"]}
    assert "labevents" in tables
    assert "emar" in tables
    for p in body["provenance"]:
        assert p["table"] and p["field"] and p["row_id"] is not None and p["time"]
    summary_l = body["summary"].lower()
    assert "earliest" in summary_l


def test_event_ordering_resolves_beyond_labs_and_meds() -> None:
    """Ordering sides resolve across full timeline taxonomy (admit + ICU observation)."""
    sid, hadm = 10039708, 28258130
    earliest_admit = "2140-01-23 16:19:00"
    earliest_hr = "2140-01-23 19:00:00"
    question = "Did admission happen before Heart Rate?"
    interp = _ScriptedInterpreter(
        "fake",
        TemplateChoice(
            template_id="event_ordering",
            slots={"event_a": "Admitted", "event_b": "Heart Rate"},
        ),
    )
    with _client_with(interp) as c:
        res = c.post(
            "/api/qa",
            json={"question": question, "subject_id": sid, "hadm_id": hadm},
        )
    assert res.status_code == 200
    body = res.json()
    assert body["kind"] == "grounded"
    by_role = {r["role"]: r for r in body["rows"] if "role" in r}
    assert by_role["event_a"]["event_time"] == earliest_admit
    assert by_role["event_b"]["event_time"] == earliest_hr
    assert by_role["ordering"]["a_before_b"] is True
    tables = {p["table"] for p in body["provenance"]}
    assert "admissions" in tables
    assert "chartevents" in tables
    assert "earliest" in body["summary"].lower()


def test_event_ordering_ignores_empty_string_hadm_slot_and_no_data_when_side_missing() -> None:
    """LLM may send hadm_id=''; must not INT64-crash; missing side → No-Data."""
    # Admission without heparin administrations (browser F2b case pattern).
    sid, hadm = 10000032, 29079034
    question = "Did the first creatinine lab happen before the first heparin administration?"
    interp = _ScriptedInterpreter(
        "fake",
        TemplateChoice(
            template_id="event_ordering",
            slots={
                "event_a": "creatinine",
                "event_b": "heparin",
                "hadm_id": "",
            },
        ),
    )
    with _client_with(interp) as c:
        res = c.post(
            "/api/qa",
            json={"question": question, "subject_id": sid, "hadm_id": hadm},
        )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["kind"] in ("grounded", "no_data")
    assert body["kind"] != "abstention"
    assert "Could not convert" not in body.get("summary", "")
    assert "INT64" not in body.get("summary", "")
    if body["kind"] == "no_data":
        assert body["coverage"]


def test_qa_examples(client: TestClient) -> None:
    res = client.get("/api/qa/examples")
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
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["patient_count"] == 100
    assert "schema" in body["egress_note"].lower() or "Patient rows never" in body["egress_note"]
