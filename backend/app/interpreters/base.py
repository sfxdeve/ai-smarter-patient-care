from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol


@dataclass
class TemplateChoice:
    template_id: str
    slots: dict[str, Any] = field(default_factory=dict)


@dataclass
class Abstain:
    reason: str
    trigger: Literal["no_template", "clinical_advice"] = "no_template"


InterpretResult = TemplateChoice | Abstain


class QuestionInterpreter(Protocol):
    name: str

    def interpret(
        self,
        question: str,
        schema: str,
        catalog: list[dict[str, Any]],
    ) -> InterpretResult: ...
