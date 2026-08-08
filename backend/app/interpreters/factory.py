from __future__ import annotations

from app.config import get_settings
from app.interpreters.base import QuestionInterpreter
from app.interpreters.fake import FakeInterpreter
from app.interpreters.keyword import KeywordBaselineInterpreter
from app.interpreters.llm import DeepSeekInterpreter


def get_interpreter(name: str | None = None) -> QuestionInterpreter:
    settings = get_settings()
    choice = (name or settings.interpreter).lower()
    if choice == "fake":
        return FakeInterpreter()
    if choice == "keyword":
        return KeywordBaselineInterpreter()
    if choice == "llm":
        return DeepSeekInterpreter()
    raise ValueError(f"Unknown interpreter: {choice}")
