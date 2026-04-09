from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from redis import Redis
from sqlalchemy.orm import Session

from app.core.errors import ValidationError
from app.dataset_export import export_train_dataset
from app.db.session import get_db_session
from app.redis_client import get_redis
from app.schemas import MetricsResponse
from app.services.metrics import read_metrics
from app.services.reservations import sync_expired_reservations

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/expired-reservations/sync", response_model=dict)
def api_sync_expired_reservations(
    limit: int = Query(default=500, ge=1, le=5000),
    db: Session = Depends(get_db_session),
    redis_client: Redis = Depends(get_redis),
) -> dict:
    result = sync_expired_reservations(db, redis_client, limit=limit)
    return {"processed": result.processed, "expired": result.expired}


@router.get("/metrics", response_model=MetricsResponse)
def api_read_metrics(
    db: Session = Depends(get_db_session),
    redis_client: Redis = Depends(get_redis),
) -> MetricsResponse:
    data = read_metrics(db, redis_client)
    return MetricsResponse(**data)


@router.get("/train-dataset")
def api_export_train_dataset(
    mode: str = Query(default="full", pattern="^(full|period|incremental)$"),
    fmt: str = Query(default="csv", pattern="^(csv|jsonl)$"),
    from_dt: str | None = Query(default=None),
    to_dt: str | None = Query(default=None),
    db: Session = Depends(get_db_session),
) -> StreamingResponse:
    parsed_from = None
    parsed_to = None
    if mode == "period":
        if from_dt is None or to_dt is None:
            raise ValidationError(
                code="invalid_period",
                message="from_dt and to_dt are required for period mode",
            )
        parsed_from = datetime.fromisoformat(from_dt)
        parsed_to = datetime.fromisoformat(to_dt)
        if parsed_from.tzinfo is None:
            parsed_from = parsed_from.replace(tzinfo=timezone.utc)
        if parsed_to.tzinfo is None:
            parsed_to = parsed_to.replace(tzinfo=timezone.utc)

    generator, content_type = export_train_dataset(
        db,
        mode=mode,  # type: ignore[arg-type]
        fmt=fmt,  # type: ignore[arg-type]
        from_dt=parsed_from,
        to_dt=parsed_to,
    )
    return StreamingResponse(generator, media_type=content_type)

