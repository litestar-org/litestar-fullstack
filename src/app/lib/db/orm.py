"""Application ORM configuration."""

from __future__ import annotations

from typing import Any

from litestar.contrib.sqlalchemy.base import AuditColumns, meta
from litestar.contrib.sqlalchemy.base import Base as DatabaseModel
from litestar.contrib.sqlalchemy.repository import ModelT  # noqa: TCH002
from sqlalchemy import String
from sqlalchemy.orm import (
    Mapped,
    declarative_mixin,
    mapped_column,
)

__all__ = ["DatabaseModel", "meta", "model_from_dict", "AuditColumns", "SlugKey"]


@declarative_mixin
class SlugKey:
    """Slug unique Field Model Mixin."""

    __abstract__ = True
    slug: Mapped[str] = mapped_column(String(length=100), index=True, nullable=False, unique=True, sort_order=-9)


def model_from_dict(model: type[ModelT], **kwargs: Any) -> ModelT:
    """Return ORM Object from Dictionary."""
    data = {}
    for column in model.__table__.columns:
        if column.name in kwargs:
            data.update({column.name: kwargs.get(column.name)})
    return model(**data)  # type: ignore[return-value]
