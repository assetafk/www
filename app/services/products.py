from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Product


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

