from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ReservationStatus(str, enum.Enum):
    active = "active"
    confirmed = "confirmed"
    cancelled = "cancelled"
    expired = "expired"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (CheckConstraint("stock >= 0", name="ck_products_stock_non_negative"),)

    reservations: Mapped[list["Reservation"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus, name="reservation_status"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    product: Mapped["Product"] = relationship(back_populates="reservations")
    outbox_events: Mapped[list["OutboxEvent"]] = relationship(
        back_populates="reservation",
        cascade="all, delete-orphan",
    )


Index("ix_reservations_user_id", Reservation.user_id)
Index("ix_reservations_status", Reservation.status)
Index("ix_reservations_product_id", Reservation.product_id)


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    reservation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("reservations.id", ondelete="CASCADE"),
        nullable=False,
    )

    reservation: Mapped["Reservation"] = relationship(back_populates="outbox_events")


class StructuredEventRow(Base):
    __tablename__ = "structured_events"

    event_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    reservation_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    reservation_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ttl_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    outbox_event_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    metric_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    extra: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


Index("ix_structured_events_type_time", StructuredEventRow.event_type, StructuredEventRow.occurred_at)
Index("ix_structured_events_reservation", StructuredEventRow.reservation_id)


class TrainDatasetCursor(Base):
    __tablename__ = "train_dataset_cursors"

    name: Mapped[str] = mapped_column(String(50), primary_key=True)
    last_final_event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

