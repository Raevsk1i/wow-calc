from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.config import get_settings
from app.persistence.db import init_db


def create_app() -> FastAPI:
    settings = get_settings()
    init_db()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="WoW DPS Lab API — SimulationCraft-backed DPS simulation for Midnight 12.1.5",
    )
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(v1_router, prefix=settings.api_prefix)
    return app


app = create_app()
