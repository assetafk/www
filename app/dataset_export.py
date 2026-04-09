from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.db.models import StructuredEventRow, TrainDatasetCursor

FINAL_EVENT_TYPES: set[str] = {
    "reservation_confirmed",
    "reservation_cancelled",
    "reservation_expired",
}

def _target_class(final_event_type: str) -> str:
    if final_event_type == "reservation_confirmed":
        return "confirmed"
    if final_event_type == "reservation_cancelled":
        return "cancelled"
    if final_event_type == "reservation_expired":
        return "expired"
    raise ValueError(f"Unknown final_event_type: {final_event_type}")


@dataclass(frozen=True)
class TrainRow:
    reservation_id: UUID
    user_id: str
    product_id: UUID
    created_at: datetime
    expires_at: datetime | None
    ttl_seconds: int | None
    final_event_type: str
    final_event_at: datetime
    target_class: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "reservation_id": str(self.reservation_id),
            "user_id": self.user_id,
            "product_id": str(self.product_id),
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "ttl_seconds": self.ttl_seconds,
            "final_event_type": self.final_event_type,
            "final_event_at": self.final_event_at.isoformat(),
            "target_class": self.target_class,
        }


def _query_rows(
    db: Session,
    *,
    from_dt: datetime | None,
    to_dt: datetime | None,
    incremental_after: datetime | None,
) -> list[TrainRow]:
    created = (
        select(
            StructuredEventRow.reservation_id.label("reservation_id"),
            StructuredEventRow.user_id.label("user_id"),
            StructuredEventRow.product_id.label("product_id"),
            StructuredEventRow.occurred_at.label("created_at"),
            StructuredEventRow.expires_at.label("expires_at"),
            StructuredEventRow.ttl_seconds.label("ttl_seconds"),
        )
        .where(StructuredEventRow.event_type == "reservation_created")
        .where(StructuredEventRow.reservation_id.is_not(None))
        .subquery("created")
    )

    final_cond = [StructuredEventRow.event_type.in_(sorted(FINAL_EVENT_TYPES))]
    final_cond.append(StructuredEventRow.reservation_id.is_not(None))
    if from_dt is not None:
        final_cond.append(StructuredEventRow.occurred_at >= from_dt)
    if to_dt is not None:
        final_cond.append(StructuredEventRow.occurred_at < to_dt)
    if incremental_after is not None:
        final_cond.append(StructuredEventRow.occurred_at > incremental_after)

    finals = (
        select(
            StructuredEventRow.reservation_id.label("reservation_id"),
            StructuredEventRow.event_type.label("final_event_type"),
            StructuredEventRow.occurred_at.label("final_event_at"),
        )
        .where(and_(*final_cond))
        .subquery("finals")
    )

    stmt = (
        select(
            created.c.reservation_id,
            created.c.user_id,
            created.c.product_id,
            created.c.created_at,
            created.c.expires_at,
            created.c.ttl_seconds,
            finals.c.final_event_type,
            finals.c.final_event_at,
        )
        .join(finals, created.c.reservation_id == finals.c.reservation_id)
        .order_by(finals.c.final_event_at.asc())
    )

    rows: list[TrainRow] = []
    for r in db.execute(stmt).all():
        rows.append(
            TrainRow(
                reservation_id=r.reservation_id,
                user_id=r.user_id,
                product_id=r.product_id,
                created_at=r.created_at,
                expires_at=r.expires_at,
                ttl_seconds=r.ttl_seconds,
                final_event_type=r.final_event_type,
                final_event_at=r.final_event_at,
                target_class=_target_class(r.final_event_type),
            )
        )
    return rows


def export_train_dataset(
    db: Session,
    *,
    mode: Literal["full", "period", "incremental"],
    fmt: Literal["csv", "jsonl"],
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
    cursor_name: str = "default",
) -> tuple[Iterator[bytes], str]:
    incremental_after: datetime | None = None
    if mode == "incremental":
        cursor = db.get(TrainDatasetCursor, cursor_name)
        if cursor is None:
            cursor = TrainDatasetCursor(name=cursor_name, last_final_event_at=datetime(1970, 1, 1, tzinfo=timezone.utc))
            db.add(cursor)
            db.commit()
            db.refresh(cursor)
        incremental_after = cursor.last_final_event_at

    rows = _query_rows(
        db,
        from_dt=from_dt if mode == "period" else None,
        to_dt=to_dt if mode == "period" else None,
        incremental_after=incremental_after,
    )

    if mode == "incremental" and rows:
        new_last = max(r.final_event_at for r in rows)
        cursor = db.execute(
            select(TrainDatasetCursor)
            .where(TrainDatasetCursor.name == cursor_name)
            .with_for_update()
        ).scalar_one()
        if new_last > cursor.last_final_event_at:
            cursor.last_final_event_at = new_last
            db.commit()

    if fmt == "jsonl":
        content_type = "application/x-ndjson"

        def gen() -> Iterator[bytes]:
            for r in rows:
                yield (json.dumps(r.to_dict(), ensure_ascii=False) + "\n").encode("utf-8")

        return gen(), content_type

    content_type = "text/csv"

    def gen_csv() -> Iterator[bytes]:
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "reservation_id",
                "user_id",
                "product_id",
                "created_at",
                "expires_at",
                "ttl_seconds",
                "final_event_type",
                "final_event_at",
                "target_class",
            ],
        )
        writer.writeheader()
        yield output.getvalue().encode("utf-8")
        output.seek(0)
        output.truncate(0)

        for r in rows:
            writer.writerow(r.to_dict())
            yield output.getvalue().encode("utf-8")
            output.seek(0)
            output.truncate(0)

    return gen_csv(), content_type

