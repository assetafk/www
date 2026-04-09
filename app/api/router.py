from __future__ import annotations

from fastapi import APIRouter

from app.api.admin import router as admin_router
from app.api.products import router as products_router
from app.api.reservations import router as reservations_router

router = APIRouter()
router.include_router(products_router)
router.include_router(reservations_router)
router.include_router(admin_router)

