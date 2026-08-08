from __future__ import annotations

from app.templates.catalog import CATALOG, TEMPLATE_BY_ID


def test_catalog_has_fourteen_templates() -> None:
    assert len(CATALOG) == 14
    assert len(TEMPLATE_BY_ID) == 14
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
    assert required == set(TEMPLATE_BY_ID)
