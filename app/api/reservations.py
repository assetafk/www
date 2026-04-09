from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from redis import Redis
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.redis_client import get_redis
from app.schemas import ReservationCreateRequest, ReservationListResponse, ReservationResponse
from app.services.reservations import (
    cancel_reservation,
    confirm_reservation,
    create_reservation,
    get_reservation,
    list_reservations,
)

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.post("", response_model=ReservationResponse, status_code=201)
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


@router.get("/{reservation_id}", response_model=ReservationResponse)
def api_get_reservation(
    reservation_id: UUID,
    db: Session = Depends(get_db_session),
) -> ReservationResponse:
    reservation = get_reservation(db, reservation_id)
    return ReservationResponse.model_validate(reservation, from_attributes=True)


@router.post("/{reservation_id}/confirm", response_model=ReservationResponse)
def api_confirm_reservation(
    reservation_id: UUID,
    db: Session = Depends(get_db_session),
    redis_client: Redis = Depends(get_redis),
) -> ReservationResponse:
    reservation = confirm_reservation(db, redis_client, reservation_id=reservation_id)
    return ReservationResponse.model_validate(reservation, from_attributes=True)


@router.post("/{reservation_id}/cancel", response_model=ReservationResponse)
def api_cancel_reservation(
    reservation_id: UUID,
    db: Session = Depends(get_db_session),
    redis_client: Redis = Depends(get_redis),
) -> ReservationResponse:
    reservation = cancel_reservation(db, redis_client, reservation_id=reservation_id)
    return ReservationResponse.model_validate(reservation, from_attributes=True)


@router.get("", response_model=ReservationListResponse)
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

