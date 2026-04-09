from __future__ import annotations

import json
import logging
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import UUID, uuid4


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


@dataclass(frozen=True)
class StructuredEvent:
    event_id: UUID = field(default_factory=uuid4)
    event_type: str = ""
    occurred_at: datetime = field(default_factory=_utc_now)

    reservation_id: UUID | None = None
    user_id: str | None = None
    product_id: UUID | None = None

    reservation_status: str | None = None
    expires_at: datetime | None = None
    ttl_seconds: int | None = None
    outbox_event_type: str | None = None
    metric_name: str | None = None

    extra: Mapping[str, Any] = field(default_factory=dict)

    def to_log_dict(self) -> dict[str, Any]:
        dct = asdict(self)
        for key in ("event_id", "reservation_id", "product_id"):
            val = dct.get(key)
            if isinstance(val, UUID):
                dct[key] = str(val)
        occurred_at = dct["occurred_at"]
        expires_at = dct["expires_at"]
        dct["occurred_at"] = occurred_at.isoformat()
        if expires_at is not None:
            dct["expires_at"] = expires_at.isoformat()
        dct["extra"] = dict(self.extra)
        return dct


def configure_logging(level: str) -> None:
    root = logging.getLogger()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter("%(message)s"))

    root.handlers.clear()
    root.addHandler(handler)


def log_request_unhandled_exception(
    *,
    request_id: str,
    method: str,
    path: str,
    exc: Exception,
) -> None:
    logging.getLogger("http").exception(
        json.dumps(
            {
                "event_type": "request_unhandled_exception",
                "request_id": request_id,
                "method": method,
                "path": path,
            },
            ensure_ascii=False,
        ),
        exc_info=exc,
    )


def log_structured_event(
    *,
    event_type: str,
    reservation_id: UUID | None = None,
    user_id: str | None = None,
    product_id: UUID | None = None,
    reservation_status: str | None = None,
    expires_at: datetime | None = None,
    ttl_seconds: int | None = None,
    outbox_event_type: str | None = None,
    metric_name: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> StructuredEvent:
    event = StructuredEvent(
        event_type=event_type,
        reservation_id=reservation_id,
        user_id=user_id,
        product_id=product_id,
        reservation_status=reservation_status,
        expires_at=expires_at,
        ttl_seconds=ttl_seconds,
        outbox_event_type=outbox_event_type,
        metric_name=metric_name,
        extra=extra or {},
    )
    logging.getLogger("structured").info(json.dumps(event.to_log_dict(), ensure_ascii=False))
    return event

