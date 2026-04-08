from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import Response

from app.middleware.http import request_logging_and_errors_middleware
from app.logging import configure_logging
from app.routers import router as api_router
from app.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title="Flash-Sale Reservations")

    @app.middleware("http")
    async def request_logging_and_errors(request: Request, call_next) -> Response:
        return await request_logging_and_errors_middleware(request, call_next)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router)

    logging.getLogger(__name__).info("app_started")
    return app


app = create_app()

