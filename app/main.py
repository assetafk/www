from __future__ import annotations

import logging

from fastapi import FastAPI

from app.api.router import router as api_router
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging
from app.core.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title="Flash-Sale Reservations")
    register_exception_handlers(app)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router)

    logging.getLogger(__name__).info("app_started")
    return app


app = create_app()

