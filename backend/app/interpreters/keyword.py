"""Keyword-matching baseline interpreter (rubric comparison + LLM outage rescue)."""

from __future__ import annotations

import re
from typing import Any

from app.interpreters.base import Abstain, InterpretResult, TemplateChoice

CLINICAL_PATTERNS = [
    r"\bdiagnos",
    r"\btreat",
    r"\btriage\b",
    r"\bshould (i|we|the patient)\b",
    r"\brecommend",
    r"\bprognos",
    r"\bwhat(?:'s| is) wrong\b",
    r"\bprescrib",
]


class KeywordBaselineInterpreter:
    name = "keyword"

    def interpret(
        self,
        question: str,
        schema: str,
        catalog: list[dict[str, Any]],
    ) -> InterpretResult:
        q = question.lower().strip()
        for pat in CLINICAL_PATTERNS:
            if re.search(pat, q):
                return Abstain(
                    reason=(
                        "Out of scope: this tool is a research and educational prototype only "
                        "and does not provide diagnosis, treatment, or triage advice."
                    ),
                    trigger="clinical_advice",
                )

        # Ordering
        if "before" in q or "after" in q or "earlier than" in q:
            a, b = _extract_pair(q)
            if not a or not b:
                return Abstain(
                    reason=(
                        "Keyword baseline could not extract both event names for ordering; "
                        "refusing rather than guessing slots."
                    ),
                    trigger="no_template",
                )
            return TemplateChoice(
                template_id="event_ordering",
                slots={"event_a": a, "event_b": b},
            )

        if "how many" in q or "count" in q or "number of" in q:
            target = "transfers"
            if "lab" in q:
                target = "labs"
            elif "med" in q or "drug" in q or "emar" in q:
                target = "medications"
            elif "procedure" in q:
                target = "procedures"
            elif "icu" in q:
                target = "icu_stays"
            return TemplateChoice(template_id="counts", slots={"count_target": target})

        if "overview" in q or "summarize this admission" in q:
            return TemplateChoice(template_id="admission_overview", slots={})

        if "icu stay" in q or "intensive care" in q:
            return TemplateChoice(template_id="icu_stay", slots={})

        if "transfer" in q or "care unit" in q or "location" in q:
            return TemplateChoice(template_id="transfers", slots={})

        if "micro" in q or "culture" in q or "organism" in q:
            return TemplateChoice(template_id="microbiology", slots={})

        if "procedure" in q:
            return TemplateChoice(template_id="procedures", slots={})

        if "vital" in q or "heart rate" in q or "respiratory rate" in q:
            return TemplateChoice(template_id="vitals_summary", slots={})

        if "first" in q or "last" in q or "earliest" in q or "latest" in q:
            which = "last" if ("last" in q or "latest" in q) else "first"
            lab = _extract_lab(q)
            return TemplateChoice(
                template_id="first_last",
                slots={"which": which, "event_kind": "lab", "lab_label": lab or "Potassium"},
            )

        if any(w in q for w in ("medication", "administered", "drug", "emar", "heparin", "insulin")):
            med = None
            for candidate in ("heparin", "insulin", "vancomycin", "norepinephrine", "fentanyl"):
                if candidate in q:
                    med = candidate.title()
                    break
            if med:
                return TemplateChoice(template_id="med_lookup", slots={"medication": med})
            return TemplateChoice(template_id="med_admins", slots={})

        lab = _extract_lab(q)
        if lab or "lab" in q or "trend" in q:
            if lab:
                return TemplateChoice(template_id="lab_trend", slots={"lab_label": lab})
            return TemplateChoice(template_id="labs_by_window", slots={})

        if "between" in q:
            return Abstain(
                reason="Keyword baseline could not extract a reliable time window; no safe template fit.",
                trigger="no_template",
            )

        return Abstain(reason="No Query Template fits this question.", trigger="no_template")


def _extract_lab(q: str) -> str | None:
    labs = [
        "creatinine",
        "potassium",
        "sodium",
        "glucose",
        "hemoglobin",
        "hematocrit",
        "wbc",
        "white blood",
        "platelet",
        "lactate",
        "troponin",
        "bun",
        "urea nitrogen",
        "magnesium",
        "chloride",
        "bicarbonate",
    ]
    for lab in labs:
        if lab in q:
            return lab.title() if lab != "wbc" else "White Blood Cells"
    return None


def _extract_pair(q: str) -> tuple[str | None, str | None]:
    patterns = [
        r"did (?:the first )?(.+?) lab happen before (?:the first )?(.+?) administration",
        r"did (?:the first )?(.+?) happen before (?:the first )?(.+?)[\?\.]?$",
        r"did (.+?) happen before (.+?)[\?\.]?$",
    ]
    for pat in patterns:
        m = re.search(pat, q)
        if m:
            a = m.group(1).strip().removeprefix("the first ").strip()
            b = m.group(2).strip().removeprefix("the first ").strip()
            b = re.sub(r"\s+administration$", "", b).strip()
            a = re.sub(r"\s+lab$", "", a).strip()
            return a or None, b or None
    parts = re.split(r"\bbefore\b|\bafter\b", q)
    if len(parts) >= 2:
        return _extract_lab(parts[0]), _extract_lab(parts[1])
    return None, None
