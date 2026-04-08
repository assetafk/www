from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from redis import Redis
from sqlalchemy.orm import Session

from app.dataset_export import export_train_dataset
from app.db import get_db_session
from app.errors import ValidationError
from app.redis_client import get_redis
from app.schemas import (
    MetricsResponse,
    ProductCreateRequest,
    ProductResponse,
    ReservationCreateRequest,
    ReservationListResponse,
    ReservationResponse,
)
from app.services import (
    cancel_reservation,
    confirm_reservation,
    create_product,
    create_reservation,
    get_reservation,
    list_products,
    list_reservations,
    read_metrics,
    sync_expired_reservations,
)

router = APIRouter()


@router.post("/products", response_model=ProductResponse, status_code=201)
def api_create_product(
    body: ProductCreateRequest,
    db: Session = Depends(get_db_session),
) -> ProductResponse:
    product = create_product(db, name=body.name, stock=body.stock)
    return ProductResponse.model_validate(product, from_attributes=True)


@router.get("/products", response_model=dict)
def api_list_products(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
) -> dict:
    items, total = list_products(db, limit=limit, offset=offset)
    return {
        "items": [ProductResponse.model_validate(p, from_attributes=True) for p in items],
        "limit": limit,
        "offset": offset,
        "total": total,
    }


@router.post("/reservations", response_model=ReservationResponse, status_code=201)
def api_create_reservation(
    body: ReservationCreateRequest,
    db: Session = Depends(get_db_session),
    redis_client: Redis = Depends(get_redis),
) -> ReservationResponse:
    reservation = create_reservation(
        db,
        redis_client,
        user_id=body.user_id,
        product_id=body.product_id,
    )
    return ReservationResponse.model_validate(reservation, from_attributes=True)


@router.get("/reservations/{reservation_id}", response_model=ReservationResponse)
def api_get_reservation(
    reservation_id: UUID,
    db: Session = Depends(get_db_session),
) -> ReservationResponse:
    reservation = get_reservation(db, reservation_id)
    return ReservationResponse.model_validate(reservation, from_attributes=True)


@router.post("/reservations/{reservation_id}/confirm", response_model=ReservationResponse)
def api_confirm_reservation(
    reservation_id: UUID,
    db: Session = Depends(get_db_session),
    redis_client: Redis = Depends(get_redis),
) -> ReservationResponse:
    reservation = confirm_reservation(db, redis_client, reservation_id=reservation_id)
    return ReservationResponse.model_validate(reservation, from_attributes=True)


@router.post("/reservations/{reservation_id}/cancel", response_model=ReservationResponse)
def api_cancel_reservation(
    reservation_id: UUID,
    db: Session = Depends(get_db_session),
    redis_client: Redis = Depends(get_redis),
) -> ReservationResponse:
    reservation = cancel_reservation(db, redis_client, reservation_id=reservation_id)
    return ReservationResponse.model_validate(reservation, from_attributes=True)


@router.get("/reservations", response_model=ReservationListResponse)
def api_list_reservations(
    user_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
) -> ReservationListResponse:
    items, total = list_reservations(
        db,
        user_id=user_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return ReservationListResponse(
        items=[ReservationResponse.model_validate(r, from_attributes=True) for r in items],
        limit=limit,
        offset=offset,
        total=total,
    )


@router.post("/admin/expired-reservations/sync", response_model=dict)
def api_sync_expired_reservations(
    limit: int = Query(default=500, ge=1, le=5000),
    db: Session = Depends(get_db_session),
    redis_client: Redis = Depends(get_redis),
) -> dict:
    result = sync_expired_reservations(db, redis_client, limit=limit)
    return {"processed": result.processed, "expired": result.expired}


@router.get("/admin/metrics", response_model=MetricsResponse)
def api_read_metrics(
    db: Session = Depends(get_db_session),
    redis_client: Redis = Depends(get_redis),
) -> MetricsResponse:
    data = read_metrics(db, redis_client)
    return MetricsResponse(**data)


@router.get("/admin/train-dataset")
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

