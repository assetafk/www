"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-07

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE reservation_status AS ENUM ('active', 'confirmed', 'cancelled', 'expired');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("stock >= 0", name="ck_products_stock_non_negative"),
    )

    op.create_table(
        "reservations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=100), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "active",
                "confirmed",
                "cancelled",
                "expired",
                name="reservation_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_reservations_user_id", "reservations", ["user_id"])
    op.create_index("ix_reservations_status", "reservations", ["status"])
    op.create_index("ix_reservations_product_id", "reservations", ["product_id"])

    op.execute(
        """
        CREATE UNIQUE INDEX uq_active_reservation_per_user_product
        ON reservations (user_id, product_id)
        WHERE status = 'active'
        """
    )

    op.create_table(
        "outbox_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("reservation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["reservation_id"], ["reservations.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "structured_events",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reservation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", sa.String(length=100), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reservation_status", sa.String(length=50), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ttl_seconds", sa.Integer(), nullable=True),
        sa.Column("outbox_event_type", sa.String(length=100), nullable=True),
        sa.Column("metric_name", sa.String(length=100), nullable=True),
        sa.Column("extra", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_structured_events_type_time",
        "structured_events",
        ["event_type", "occurred_at"],
    )
    op.create_index("ix_structured_events_reservation", "structured_events", ["reservation_id"])

    op.create_table(
        "train_dataset_cursors",
        sa.Column("name", sa.String(length=50), primary_key=True, nullable=False),
        sa.Column("last_final_event_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("train_dataset_cursors")
    op.drop_index("ix_structured_events_reservation", table_name="structured_events")
    op.drop_index("ix_structured_events_type_time", table_name="structured_events")
    op.drop_table("structured_events")
    op.drop_table("outbox_events")

    op.execute("DROP INDEX IF EXISTS uq_active_reservation_per_user_product")
    op.drop_index("ix_reservations_product_id", table_name="reservations")
    op.drop_index("ix_reservations_status", table_name="reservations")
    op.drop_index("ix_reservations_user_id", table_name="reservations")
    op.drop_table("reservations")

    op.drop_table("products")
    op.execute("DROP TYPE IF EXISTS reservation_status")

