from __future__ import annotations

from redis import Redis
from sqlalchemy.orm import Session


def _metrics_key() -> str:
    return "metrics:reservations"


def read_metrics(db: Session, redis_client: Redis) -> dict[str, int]:
    raw = redis_client.hgetall(_metrics_key())
    data = {k: int(v) for k, v in raw.items()}
    return {
        "created": int(data.get("created", 0)),
        "confirmed": int(data.get("confirmed", 0)),
        "cancelled": int(data.get("cancelled", 0)),
        "expired": int(data.get("expired", 0)),
    }

