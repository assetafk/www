from __future__ import annotations

import json
import logging
import time
from uuid import uuid4

from fastapi import Request
from fastapi.responses import Response


def get_or_create_request_id(request: Request) -> str:
    return request.headers.get("x-request-id") or str(uuid4())


def attach_request_id(response: Response, request_id: str) -> None:
    response.headers["x-request-id"] = request_id


def log_request(*, request: Request, response: Response, request_id: str, start_perf_counter: float) -> None:
    duration_ms = (time.perf_counter() - start_perf_counter) * 1000.0
    logging.getLogger("http").info(
        json.dumps(
            {
                "event_type": "request",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": request.url.query,
                "status_code": getattr(response, "status_code", None),
                "duration_ms": round(duration_ms, 2),
                "client": request.client.host if request.client else None,
            },
            ensure_ascii=False,
        )
    )


def log_unhandled_exception(*, request: Request, request_id: str) -> None:
    logging.getLogger("http").exception(
        json.dumps(
            {
                "event_type": "request_unhandled_exception",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
            },
            ensure_ascii=False,
        )
    )

