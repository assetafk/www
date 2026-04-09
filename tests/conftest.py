from __future__ import annotations

import os
from pathlib import Path

# Configure before importing app (lazy engine reads DATABASE_URL on first use).
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg2://flashsale:flashsale@127.0.0.1:5432/flashsale_test",
)
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6379/15")

import fakeredis
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import dispose_engine, get_engine
from app.main import app
from app.redis_client import get_redis


@pytest.fixture(scope="session", autouse=True)
def _alembic_upgrade() -> None:
    root = Path(__file__).resolve().parent.parent
    cfg = Config(str(root / "alembic.ini"))
    command.upgrade(cfg, "head")
    yield
    dispose_engine()


@pytest.fixture(autouse=True)
def _clean_tables() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE TABLE outbox_events, structured_events, reservations, "
                "products, train_dataset_cursors RESTART IDENTITY CASCADE"
            )
        )
    yield


@pytest.fixture(autouse=True)
def _override_redis() -> None:
    fake = fakeredis.FakeRedis(decode_responses=True)
    app.dependency_overrides[get_redis] = lambda: fake
    yield fake
    app.dependency_overrides.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def db_session() -> Session:
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
