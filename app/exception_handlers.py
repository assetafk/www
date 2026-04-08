from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.errors import AppError, ConflictError, NotFoundError, ValidationError
from app.logging import log_request_unhandled_exception


def _request_id(request: Request) -> str:
    return request.headers.get("x-request-id") or str(uuid4())


def _with_request_id(response: JSONResponse, request_id: str) -> JSONResponse:
    response.headers["x-request-id"] = request_id
    return response


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


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        rid = _request_id(request)
        return _with_request_id(app_error_response(exc), rid)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        rid = _request_id(request)
        return _with_request_id(http_exception_response(exc), rid)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        rid = _request_id(request)
        log_request_unhandled_exception(
            request_id=rid,
            method=request.method,
            path=request.url.path,
            exc=exc,
        )
        return _with_request_id(internal_error_response(), rid)
