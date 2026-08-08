"""Scripted fake interpreter for deterministic tests."""

from __future__ import annotations

from typing import Any

from app.interpreters.base import Abstain, InterpretResult, TemplateChoice


class FakeInterpreter:
    name = "fake"

    def __init__(self, script: dict[str, InterpretResult] | None = None) -> None:
        self.script = script or {}

    def interpret(
        self,
        question: str,
        schema: str,
        catalog: list[dict[str, Any]],
    ) -> InterpretResult:
        key = question.strip().lower()
        if key in self.script:
            return self.script[key]
        # Default heuristics for common test phrases
        if "diagnose" in key or "treat" in key or "should i" in key or "triage" in key:
            return Abstain(
                reason="Out of scope: Chronicle does not provide clinical advice.",
                trigger="clinical_advice",
            )
        if "how many transfer" in key:
            return TemplateChoice(template_id="counts", slots={"count_target": "transfers"})
        if "creatinine" in key:
            return TemplateChoice(template_id="lab_trend", slots={"lab_label": "Creatinine"})
        if "medication" in key or "administered" in key or "heparin" in key:
            med = "Heparin" if "heparin" in key else None
            return TemplateChoice(
                template_id="med_admins" if not med else "med_lookup",
                slots={"medication": med} if med else {},
            )
        if "overview" in key:
            return TemplateChoice(template_id="admission_overview", slots={})
        if "icu stay" in key:
            return TemplateChoice(template_id="icu_stay", slots={})
        if "transfer" in key:
            return TemplateChoice(template_id="transfers", slots={})
        if "before" in key:
            return TemplateChoice(
                template_id="event_ordering",
                slots={"event_a": "Creatinine", "event_b": "Heparin"},
            )
        if "unanswerable" in key or "favorite color" in key:
            return Abstain(reason="No Query Template fits this question.", trigger="no_template")
        return Abstain(reason="No Query Template fits this question.", trigger="no_template")
