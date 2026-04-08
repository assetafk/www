from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: dict[str, str]


class ProductCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    stock: int = Field(ge=0)


class ProductResponse(BaseModel):
    id: UUID
    name: str
    stock: int
    created_at: datetime


class ReservationCreateRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    product_id: UUID


class ReservationResponse(BaseModel):
    id: UUID
    user_id: str
    product_id: UUID
    status: str
    created_at: datetime
    expires_at: datetime
    updated_at: datetime


class ReservationListResponse(BaseModel):
    items: list[ReservationResponse]
    limit: int
    offset: int
    total: int


class MetricsResponse(BaseModel):
    created: int
    confirmed: int
    cancelled: int
    expired: int

