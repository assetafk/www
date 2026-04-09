from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import fakeredis
from sqlalchemy import func, select, update
from sqlalchemy.orm import sessionmaker

from app.core.errors import ConflictError
from app.db.models import OutboxEvent, Product, Reservation, ReservationStatus
from app.db.session import get_engine
from app.services.reservations import create_reservation, sync_expired_reservations


def _create_product(client, *, name: str = "Item", stock: int = 10) -> UUID:
    r = client.post("/products", json={"name": name, "stock": stock})
    assert r.status_code == 201, r.text
    return UUID(r.json()["id"])


def test_happy_path_create_reserve_confirm(client, db_session) -> None:
    product_id = _create_product(client, stock=2)

    res = client.post(
        "/reservations",
        json={"user_id": "user-1", "product_id": str(product_id)},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    reservation_id = UUID(body["id"])
    assert body["status"] == "active"

    stock_after_reserve = db_session.scalar(select(Product.stock).where(Product.id == product_id))
    assert stock_after_reserve == 1

    conf = client.post(f"/reservations/{reservation_id}/confirm")
    assert conf.status_code == 200, conf.text
    assert conf.json()["status"] == "confirmed"

    outbox = db_session.scalar(
        select(func.count()).select_from(OutboxEvent).where(OutboxEvent.reservation_id == reservation_id)
    )
    assert int(outbox) == 1

    stock_after_confirm = db_session.scalar(select(Product.stock).where(Product.id == product_id))
    assert stock_after_confirm == 1


def test_expiry_via_sync_restores_stock(client, db_session) -> None:
    product_id = _create_product(client, stock=2)

    res = client.post(
        "/reservations",
        json={"user_id": "user-exp", "product_id": str(product_id)},
    )
    assert res.status_code == 201, res.text
    reservation_id = UUID(res.json()["id"])

    assert db_session.scalar(select(Product.stock).where(Product.id == product_id)) == 1

    created_raw = res.json()["created_at"]
    created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
    db_session.execute(
        update(Reservation)
        .where(Reservation.id == reservation_id)
        .values(expires_at=created_at - timedelta(minutes=5))
    )
    db_session.commit()

    sync = client.post("/admin/expired-reservations/sync")
    assert sync.status_code == 200, sync.text
    assert sync.json()["expired"] >= 1

    db_session.expire_all()
    status = db_session.scalar(select(Reservation.status).where(Reservation.id == reservation_id))
    assert status == ReservationStatus.expired
    assert db_session.scalar(select(Product.stock).where(Product.id == product_id)) == 2


def test_cancel_restores_stock(client, db_session) -> None:
    product_id = _create_product(client, stock=2)

    res = client.post(
        "/reservations",
        json={"user_id": "user-can", "product_id": str(product_id)},
    )
    assert res.status_code == 201, res.text
    reservation_id = UUID(res.json()["id"])

    assert db_session.scalar(select(Product.stock).where(Product.id == product_id)) == 1

    cancel = client.post(f"/reservations/{reservation_id}/cancel")
    assert cancel.status_code == 200, cancel.text
    assert cancel.json()["status"] == "cancelled"

    assert db_session.scalar(select(Product.stock).where(Product.id == product_id)) == 2


def test_no_second_active_reservation_same_user_product(client) -> None:
    product_id = _create_product(client, stock=2)

    first = client.post(
        "/reservations",
        json={"user_id": "same-user", "product_id": str(product_id)},
    )
    assert first.status_code == 201, first.text

    second = client.post(
        "/reservations",
        json={"user_id": "same-user", "product_id": str(product_id)},
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "active_reservation_exists"


def test_concurrent_last_unit_only_one_succeeds() -> None:
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    redis_client = fakeredis.FakeRedis(decode_responses=True)

    db = SessionLocal()
    try:
        product = Product(name="Hot", stock=1)
        db.add(product)
        db.commit()
        db.refresh(product)
        product_id = product.id
    finally:
        db.close()

    outcomes: list[str] = []

    def worker() -> None:
        s = SessionLocal()
        try:
            create_reservation(s, redis_client, user_id=f"u-{uuid4()}", product_id=product_id)
            outcomes.append("created")
        except ConflictError as exc:
            outcomes.append(exc.code)
        finally:
            s.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        f1 = pool.submit(worker)
        f2 = pool.submit(worker)
        f1.result()
        f2.result()

    assert sorted(outcomes) == ["created", "out_of_stock"]

    verify = SessionLocal()
    try:
        active = verify.scalars(
            select(Reservation).where(
                Reservation.product_id == product_id,
                Reservation.status == ReservationStatus.active,
            )
        ).all()
        assert len(active) == 1
        assert verify.scalar(select(Product.stock).where(Product.id == product_id)) == 0
    finally:
        verify.close()
