from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import fetchone_dict
from app.deps import get_shared_connection
from app.models import HealthResponse
from app.routes import patients, qa

SAFETY_NOTICE = (
    "Research and educational prototype only. Not for clinical use. "
    "Do not use for diagnosis, treatment, triage, or patient-specific recommendations."
)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Chronicle API", version="0.1.0")
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(patients.router)
    app.include_router(qa.router)

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        con = get_shared_connection()
        row = fetchone_dict(con, "SELECT COUNT(*) AS n FROM patients")
        n = int(row["n"]) if row else 0
        return HealthResponse(
            status="ok",
            data_dir=str(settings.data_dir),
            patient_count=n,
            llm_model=settings.llm_model,
            interpreter=settings.interpreter,
        )

    @app.get("/meta/safety-notice")
    def safety_notice() -> dict[str, str]:
        return {"notice": SAFETY_NOTICE}

    return app


app = create_app()
