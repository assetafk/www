from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppError(Exception):
    code: str
    message: str


class NotFoundError(AppError):
    pass


class ConflictError(AppError):
    pass


class ValidationError(AppError):
    pass

