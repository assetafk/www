from __future__ import annotations

import time

from fastapi import HTTPException, Request
from fastapi.responses import Response

from app.errors import AppError
from app.middleware.errors import (
    app_error_response,
    http_exception_response,
    internal_error_response,
)
from app.middleware.request_logging import (
    attach_request_id,
    get_or_create_request_id,
    log_request,
    log_unhandled_exception,
)


async def request_logging_and_errors_middleware(request: Request, call_next) -> Response:
    request_id = get_or_create_request_id(request)
    start = time.perf_counter()

    try:
        response = await call_next(request)
    except AppError as exc:
        response = app_error_response(exc)
    except HTTPException as exc:
        response = http_exception_response(exc)
    except Exception:
        log_unhandled_exception(request=request, request_id=request_id)
        response = internal_error_response()

    attach_request_id(response, request_id)
    log_request(request=request, response=response, request_id=request_id, start_perf_counter=start)
    return response

