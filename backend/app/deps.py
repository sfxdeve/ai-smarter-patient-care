from __future__ import annotations

from collections.abc import Generator
from threading import Lock

import duckdb
from fastapi import Request

from app.db import connect
from app.interpreters.base import QuestionInterpreter
from app.interpreters.factory import get_interpreter

_lock = Lock()
_shared: duckdb.DuckDBPyConnection | None = None


def get_shared_connection() -> duckdb.DuckDBPyConnection:
    """Process-wide DuckDB connection (views over CSV; safe for concurrent reads)."""
    global _shared
    with _lock:
        if _shared is None:
            _shared = connect()
        return _shared


def get_db() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    yield get_shared_connection()


def get_qa_interpreter(request: Request) -> QuestionInterpreter:
    override = getattr(request.app.state, "interpreter", None)
    if override is not None:
        return override
    return get_interpreter()


def reset_shared_connection() -> None:
    global _shared
    with _lock:
        if _shared is not None:
            _shared.close()
            _shared = None
