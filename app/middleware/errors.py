from __future__ import annotations

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from app.errors import AppError, ConflictError, NotFoundError, ValidationError


def app_error_status_code(exc: AppError) -> int:
    if isinstance(exc, NotFoundError):
        return 404
    if isinstance(exc, ConflictError):
        return 409
    if isinstance(exc, ValidationError):
        return 400
    return 400


def app_error_response(exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=app_error_status_code(exc),
        content={"error": {"code": exc.code, "message": exc.message}},
    )


def http_exception_response(exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": str(exc.detail)}},
    )


def internal_error_response() -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": "Internal Server Error"}},
    )

