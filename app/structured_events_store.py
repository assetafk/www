from __future__ import annotations

from dataclasses import asdict
from typing import Any

from sqlalchemy.orm import Session

from app.core.logging import StructuredEvent
from app.db.models import StructuredEventRow


def try_persist_structured_event(db: Session, event: StructuredEvent) -> None:
    """
    Best-effort persistence for structured events.

    Per requirements, logging must not affect core reservation flow, so failures
    are swallowed.
    """
    try:
        payload: dict[str, Any] = asdict(event)
        row = StructuredEventRow(
            event_id=payload["event_id"],
            event_type=payload["event_type"],
            occurred_at=payload["occurred_at"],
            reservation_id=payload["reservation_id"],
            user_id=payload["user_id"],
            product_id=payload["product_id"],
            reservation_status=payload["reservation_status"],
            expires_at=payload["expires_at"],
            ttl_seconds=payload["ttl_seconds"],
            outbox_event_type=payload["outbox_event_type"],
            metric_name=payload["metric_name"],
            extra=dict(payload.get("extra") or {}),
        )
        db.add(row)
        db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            return

