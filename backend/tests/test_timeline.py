from __future__ import annotations

from fastapi.testclient import TestClient


def _first_admission(client: TestClient) -> tuple[int, int]:
    patients = client.get("/patients").json()
    sid = patients[0]["subject_id"]
    detail = client.get(f"/patients/{sid}").json()
    hadm = detail["admissions"][0]["hadm_id"]
    return sid, hadm


def test_timeline_has_events_and_provenance(client: TestClient) -> None:
    sid, hadm = _first_admission(client)
    res = client.get(f"/patients/{sid}/admissions/{hadm}/timeline")
    assert res.status_code == 200
    body = res.json()
    assert body["subject_id"] == sid
    assert body["hadm_id"] == hadm
    assert len(body["events"]) >= 2  # at least admit + discharge
    for ev in body["events"]:
        prov = ev["provenance"]
        assert prov["table"]
        assert prov["field"]
        assert "row_id" in prov
    # Events are time-ordered (None times last-ish; we sort with min datetime)
    times = [e["time"] for e in body["events"] if e["time"]]
    assert times == sorted(times)


def test_billing_context_untimed(client: TestClient) -> None:
    sid, hadm = _first_admission(client)
    res = client.get(f"/patients/{sid}/admissions/{hadm}/billing-context")
    assert res.status_code == 200
    body = res.json()
    assert "untimed" in body["notice"].lower() or "Billing Context" in body["notice"]
    for d in body["diagnoses"]:
        assert d["provenance"]["time"] is None


def test_timeline_rejects_bad_window(client: TestClient) -> None:
    sid, hadm = _first_admission(client)
    res = client.get(
        f"/patients/{sid}/admissions/{hadm}/timeline",
        params={"start": "2200-01-02", "end": "2200-01-01"},
    )
    assert res.status_code == 400


def test_timeline_filter_event_types(client: TestClient) -> None:
    sid, hadm = _first_admission(client)
    res = client.get(
        f"/patients/{sid}/admissions/{hadm}/timeline",
        params={"event_types": "transfer"},
    )
    assert res.status_code == 200
    for ev in res.json()["events"]:
        assert ev["event_type"] == "transfer"


def test_icu_observation_bands_expandable(client: TestClient) -> None:
    # Find an admission with ICU observations
    patients = client.get("/patients").json()
    found = False
    for p in patients[:20]:
        detail = client.get(f"/patients/{p['subject_id']}").json()
        for adm in detail["admissions"]:
            res = client.get(
                f"/patients/{p['subject_id']}/admissions/{adm['hadm_id']}/timeline",
                params={"event_types": "icu_observation"},
            )
            events = res.json()["events"]
            bands = [e for e in events if e.get("band_key")]
            if bands:
                band = bands[0]
                assert band["band_count"] >= 1
                assert band["band_events"] is not None
                assert len(band["band_events"]) == band["band_count"]
                found = True
                break
        if found:
            break
    assert found
