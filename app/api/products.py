from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.schemas import ProductCreateRequest, ProductResponse
from app.services.products import create_product, list_products

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductResponse, status_code=201)
def api_create_product(
    body: ProductCreateRequest,
    db: Session = Depends(get_db_session),
) -> ProductResponse:
    product = create_product(db, name=body.name, stock=body.stock)
    return ProductResponse.model_validate(product, from_attributes=True)


@router.get("", response_model=dict)
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

