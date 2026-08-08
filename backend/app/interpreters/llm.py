"""DeepSeek V4-Flash interpreter via OpenCode Zen (tool/function calling)."""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from app.config import get_settings
from app.interpreters.base import Abstain, InterpretResult, TemplateChoice
from app.templates.catalog import TEMPLATE_BY_ID

SYSTEM_PROMPT = """You are the question interpreter for Chronicle, a research/education tool over MIMIC-IV Demo.
You NEVER see patient rows. You only choose a Query Template and fill slots, or abstain.

Rules:
1. Abstain with trigger clinical_advice ONLY for diagnosis, treatment, triage, prognosis, prescribing, or care-plan advice.
2. Prefer select_template whenever any catalog template could retrieve relevant structured rows
   (labs, meds, transfers, ICU stays, procedures, microbiology, vitals, counts, ordering, admission overview).
3. Abstain with trigger no_template only for clearly out-of-scope non-clinical questions (favorite color, weather, SSN, free-text notes, future prediction).
4. Do not invent SQL. Do not invent clinical facts.
5. subject_id and hadm_id are supplied by the application; omit them from slots.
6. For event_ordering ("did X happen before Y?"), set event_a and event_b to the event names copied
   literally from the question (keep dose/parenthetical text). Always use template event_ordering — never abstain.
7. For counts, set count_target to one of: transfers, labs, medications, procedures, icu_stays.
8. Mapping hints: "what labs" → labs_by_window; "trend"/named lab → lab_trend; "medications administered" → med_admins;
   "was X administered" → med_lookup; "transfers"/"where transferred" → transfers; "ICU stays" → icu_stay;
   "procedures" → procedures; "microbiology" → microbiology; "heart rate"/"vitals" → vitals_summary;
   "overview" → admission_overview; "how many" → counts.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "select_template",
            "description": "Choose a Query Template and fill its slots.",
            "parameters": {
                "type": "object",
                "properties": {
                    "template_id": {
                        "type": "string",
                        "description": "ID from the Query Template catalog",
                    },
                    "slots": {
                        "type": "object",
                        "description": "Slot values for the template",
                        "additionalProperties": True,
                    },
                },
                "required": ["template_id", "slots"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "abstain",
            "description": "Refuse to answer — no template fits or clinical advice requested.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string"},
                    "trigger": {
                        "type": "string",
                        "enum": ["no_template", "clinical_advice"],
                    },
                },
                "required": ["reason", "trigger"],
            },
        },
    },
]


class DeepSeekInterpreter:
    name = "llm"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        max_retries: int = 2,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.opencode_api_key
        self.base_url = base_url or settings.llm_base_url
        self.model = model or settings.llm_model
        self.max_retries = max_retries

    def interpret(
        self,
        question: str,
        schema: str,
        catalog: list[dict[str, Any]],
    ) -> InterpretResult:
        if not self.api_key:
            raise RuntimeError("OPENCODE_API_KEY not configured")

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        user = (
            f"SCHEMA:\n{schema}\n\n"
            f"QUERY TEMPLATE CATALOG:\n{json.dumps(catalog, indent=2)}\n\n"
            f"QUESTION:\n{question}\n\n"
            "Call select_template or abstain."
        )

        last_err: Exception | None = None
        for _ in range(self.max_retries + 1):
            try:
                resp = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user},
                    ],
                    tools=TOOLS,
                    tool_choice="required",
                    temperature=0,
                    # Zen/DeepSeek: disable thinking; JSON mode unreliable via gateway.
                    extra_body={"thinking": {"type": "disabled"}},
                )
                msg = resp.choices[0].message
                if not msg.tool_calls:
                    last_err = ValueError("No tool call in response")
                    continue
                call = msg.tool_calls[0]
                name = call.function.name
                args = json.loads(call.function.arguments or "{}")
                if name == "abstain":
                    trigger = args.get("trigger", "no_template")
                    if trigger not in ("no_template", "clinical_advice"):
                        trigger = "no_template"
                    return Abstain(reason=str(args.get("reason") or "Abstained"), trigger=trigger)
                if name == "select_template":
                    tid = args.get("template_id")
                    if tid not in TEMPLATE_BY_ID:
                        last_err = ValueError(f"Invalid template_id: {tid}")
                        continue
                    slots = args.get("slots") or {}
                    if not isinstance(slots, dict):
                        last_err = ValueError("slots must be an object")
                        continue
                    # Drop nulls
                    slots = {k: v for k, v in slots.items() if v is not None}
                    return TemplateChoice(template_id=tid, slots=slots)
                last_err = ValueError(f"Unknown tool: {name}")
            except Exception as exc:  # noqa: BLE001 — retries then raise
                last_err = exc
        assert last_err is not None
        raise last_err
