from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.interpreters.fake import FakeInterpreter
from app.main import create_app


@pytest.fixture()
def client() -> TestClient:
    app = create_app()
    app.state.interpreter = FakeInterpreter()
    with TestClient(app) as c:
        yield c
