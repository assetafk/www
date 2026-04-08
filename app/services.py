from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from redis import Redis
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import ConflictError, NotFoundError, ValidationError
from app.logging import log_structured_event
from app.models import OutboxEvent, Product, Reservation, ReservationStatus
from app.settings import get_settings
from app.structured_events_store import try_persist_structured_event


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _ttl_key(reservation_id: UUID) -> str:
    return f"reservation:ttl:{reservation_id}"


def _metrics_key() -> str:
    return "metrics:reservations"


@dataclass(frozen=True)
class SyncResult:
    processed: int
    expired: int


def create_product(db: Session, *, name: str, stock: int) -> Product:
    product = Product(name=name, stock=stock)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def list_products(db: Session, *, limit: int, offset: int) -> tuple[list[Product], int]:
    stmt = select(Product).order_by(Product.created_at.desc()).limit(limit).offset(offset)
    items = list(db.execute(stmt).scalars().all())
    total = int(db.execute(select(func.count()).select_from(Product)).scalar_one())
    return items, total


def get_reservation(db: Session, reservation_id: UUID) -> Reservation:
    reservation = db.get(Reservation, reservation_id)
    if reservation is None:
        raise NotFoundError(code="reservation_not_found", message="Reservation not found")
    return reservation


def _increment_metric(
    db: Session,
    redis_client: Redis,
    *,
    name: str,
    reservation_id: UUID | None = None,
    user_id: str | None = None,
    product_id: UUID | None = None,
    reservation_status: str | None = None,
) -> None:
    redis_client.hincrby(_metrics_key(), name, 1)
    event = log_structured_event(
        event_type="metrics_counter_incremented",
        reservation_id=reservation_id,
        user_id=user_id,
        product_id=product_id,
        reservation_status=reservation_status,
        metric_name=name,
    )
    try_persist_structured_event(db, event)


def _register_ttl(
    db: Session,
    redis_client: Redis,
    *,
    reservation_id: UUID,
    ttl_seconds: int,
    expires_at: datetime,
    user_id: str,
    product_id: UUID,
) -> None:
    redis_client.set(_ttl_key(reservation_id), "1", ex=ttl_seconds)
    event = log_structured_event(
        event_type="reservation_ttl_registered",
        reservation_id=reservation_id,
        user_id=user_id,
        product_id=product_id,
        ttl_seconds=ttl_seconds,
        expires_at=expires_at,
    )
    try_persist_structured_event(db, event)


def create_reservation(
    db: Session,
    redis_client: Redis,
    *,
    user_id: str,
    product_id: UUID,
) -> Reservation:
    settings = get_settings()
    ttl_seconds = int(settings.reservation_ttl_seconds)
    if ttl_seconds <= 0:
        raise ValidationError(code="invalid_ttl", message="Reservation TTL must be positive")

    now = _utc_now()
    expires_at = now + timedelta(seconds=ttl_seconds)

    try:
        product = db.execute(
            select(Product).where(Product.id == product_id).with_for_update()
        ).scalar_one_or_none()
        if product is None:
            raise NotFoundError(code="product_not_found", message="Product not found")

        if product.stock <= 0:
            raise ConflictError(code="out_of_stock", message="Product is out of stock")

        active_exists = db.execute(
            select(func.count())
            .select_from(Reservation)
            .where(
                and_(
                    Reservation.user_id == user_id,
                    Reservation.product_id == product_id,
                    Reservation.status == ReservationStatus.active,
                )
            )
        ).scalar_one()
        if int(active_exists) > 0:
            raise ConflictError(
                code="active_reservation_exists",
                message="Active reservation already exists for this user and product",
            )

        product.stock -= 1
        reservation = Reservation(
            user_id=user_id,
            product_id=product_id,
            status=ReservationStatus.active,
            expires_at=expires_at,
        )
        db.add(reservation)
        db.commit()
        db.refresh(reservation)
    except IntegrityError:
        db.rollback()
        raise ConflictError(
            code="active_reservation_exists",
            message="Active reservation already exists for this user and product",
        )

    event = log_structured_event(
        event_type="reservation_created",
        reservation_id=reservation.id,
        user_id=user_id,
        product_id=product_id,
        reservation_status=reservation.status.value,
        expires_at=reservation.expires_at,
        ttl_seconds=ttl_seconds,
    )
    try_persist_structured_event(db, event)

    _register_ttl(
        db,
        redis_client,
        reservation_id=reservation.id,
        ttl_seconds=ttl_seconds,
        expires_at=reservation.expires_at,
        user_id=user_id,
        product_id=product_id,
    )
    _increment_metric(
        db,
        redis_client,
        name="created",
        reservation_id=reservation.id,
        user_id=user_id,
        product_id=product_id,
        reservation_status=reservation.status.value,
    )
    return reservation


def confirm_reservation(db: Session, redis_client: Redis, *, reservation_id: UUID) -> Reservation:
    outbox_event_type = "reservation_confirmed"

    reservation = db.execute(
        select(Reservation).where(Reservation.id == reservation_id).with_for_update()
    ).scalar_one_or_none()
    if reservation is None:
        raise NotFoundError(code="reservation_not_found", message="Reservation not found")

    if reservation.status != ReservationStatus.active:
        raise ConflictError(code="invalid_status", message="Reservation is not active")

    reservation.status = ReservationStatus.confirmed

    outbox = OutboxEvent(
        id=uuid4(),
        event_type=outbox_event_type,
        payload={
            "reservation_id": str(reservation.id),
            "user_id": reservation.user_id,
            "product_id": str(reservation.product_id),
            "confirmed_at": _utc_now().isoformat(),
        },
        reservation_id=reservation.id,
    )
    db.add(outbox)
    db.commit()
    db.refresh(reservation)

    redis_client.delete(_ttl_key(reservation.id))

    event = log_structured_event(
        event_type="reservation_confirmed",
        reservation_id=reservation.id,
        user_id=reservation.user_id,
        product_id=reservation.product_id,
        reservation_status=reservation.status.value,
    )
    try_persist_structured_event(db, event)

    outbox_event = log_structured_event(
        event_type="reservation_confirmation_outbox_written",
        reservation_id=reservation.id,
        user_id=reservation.user_id,
        product_id=reservation.product_id,
        outbox_event_type=outbox_event_type,
    )
    try_persist_structured_event(db, outbox_event)

    _increment_metric(
        db,
        redis_client,
        name="confirmed",
        reservation_id=reservation.id,
        user_id=reservation.user_id,
        product_id=reservation.product_id,
        reservation_status=reservation.status.value,
    )
    return reservation


def cancel_reservation(db: Session, redis_client: Redis, *, reservation_id: UUID) -> Reservation:
    reservation = db.execute(
        select(Reservation).where(Reservation.id == reservation_id).with_for_update()
    ).scalar_one_or_none()
    if reservation is None:
        raise NotFoundError(code="reservation_not_found", message="Reservation not found")

    if reservation.status != ReservationStatus.active:
        raise ConflictError(code="invalid_status", message="Reservation is not active")

    product = db.execute(
        select(Product).where(Product.id == reservation.product_id).with_for_update()
    ).scalar_one()

    reservation.status = ReservationStatus.cancelled
    product.stock += 1
    db.commit()
    db.refresh(reservation)

    redis_client.delete(_ttl_key(reservation.id))

    event = log_structured_event(
        event_type="reservation_cancelled",
        reservation_id=reservation.id,
        user_id=reservation.user_id,
        product_id=reservation.product_id,
        reservation_status=reservation.status.value,
    )
    try_persist_structured_event(db, event)

    _increment_metric(
        db,
        redis_client,
        name="cancelled",
        reservation_id=reservation.id,
        user_id=reservation.user_id,
        product_id=reservation.product_id,
        reservation_status=reservation.status.value,
    )
    return reservation


def list_reservations(
    db: Session,
    *,
    user_id: str | None,
    status: str | None,
    limit: int,
    offset: int,
) -> tuple[list[Reservation], int]:
    cond = []
    if user_id is not None:
        cond.append(Reservation.user_id == user_id)
    if status is not None:
        try:
            parsed = ReservationStatus(status)
        except ValueError as exc:
            raise ValidationError(code="invalid_status", message="Unknown reservation status") from exc
        cond.append(Reservation.status == parsed)

    where_clause = and_(*cond) if cond else True

    stmt = (
        select(Reservation)
        .where(where_clause)
        .order_by(Reservation.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    items = list(db.execute(stmt).scalars().all())
    total_stmt = select(func.count()).select_from(Reservation).where(where_clause)
    total = int(db.execute(total_stmt).scalar_one())
    return items, total


def sync_expired_reservations(
    db: Session,
    redis_client: Redis,
    *,
    limit: int = 500,
) -> SyncResult:
    started = log_structured_event(event_type="expired_reservations_sync_started")
    try_persist_structured_event(db, started)

    now = _utc_now()
    processed = 0
    expired = 0

    candidate_ids = list(
        db.execute(
            select(Reservation.id)
            .where(
                and_(
                    Reservation.status == ReservationStatus.active,
                    Reservation.expires_at <= now,
                )
            )
            .order_by(Reservation.expires_at.asc())
            .limit(limit)
        ).scalars()
    )

    for rid in candidate_ids:
        processed += 1
        try:
            reservation = db.execute(
                select(Reservation)
                .where(Reservation.id == rid)
                .with_for_update(skip_locked=True)
            ).scalar_one_or_none()
            if reservation is None or reservation.status != ReservationStatus.active:
                db.rollback()
                continue

            if reservation.expires_at > now:
                db.rollback()
                continue

            product = db.execute(
                select(Product).where(Product.id == reservation.product_id).with_for_update()
            ).scalar_one()

            reservation.status = ReservationStatus.expired
            product.stock += 1
            db.commit()
            db.refresh(reservation)

            redis_client.delete(_ttl_key(reservation.id))

            expired += 1
            event = log_structured_event(
                event_type="reservation_expired",
                reservation_id=reservation.id,
                user_id=reservation.user_id,
                product_id=reservation.product_id,
                reservation_status=reservation.status.value,
            )
            try_persist_structured_event(db, event)

            _increment_metric(
                db,
                redis_client,
                name="expired",
                reservation_id=reservation.id,
                user_id=reservation.user_id,
                product_id=reservation.product_id,
                reservation_status=reservation.status.value,
            )
        except Exception:
            db.rollback()
            continue

    completed = log_structured_event(
        event_type="expired_reservations_sync_completed",
        extra={"processed": processed, "expired": expired},
    )
    try_persist_structured_event(db, completed)

    return SyncResult(processed=processed, expired=expired)


def read_metrics(db: Session, redis_client: Redis) -> dict[str, int]:
    raw = redis_client.hgetall(_metrics_key())
    data = {k: int(v) for k, v in raw.items()}
    return {
        "created": int(data.get("created", 0)),
        "confirmed": int(data.get("confirmed", 0)),
        "cancelled": int(data.get("cancelled", 0)),
        "expired": int(data.get("expired", 0)),
    }

