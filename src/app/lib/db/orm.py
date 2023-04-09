"""Application ORM configuration."""

from __future__ import annotations

from typing import Any

from litestar.contrib.sqlalchemy.base import AuditColumns, meta
from litestar.contrib.sqlalchemy.base import Base as DatabaseModel
from litestar.contrib.sqlalchemy.repository import ModelT  # noqa: TCH002

__all__ = ["DatabaseModel", "meta", "model_from_dict", "AuditColumns"]


def model_from_dict(model: type[ModelT], **kwargs: Any) -> ModelT:
    """Return ORM Object from Dictionary."""
    data = {}
    for column in model.__table__.columns:
        if column.name in kwargs:
            data.update({column.name: kwargs.get(column.name)})
    return model(**data)  # type: ignore[return-value]
