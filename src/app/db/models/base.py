from __future__ import annotations

from typing import TYPE_CHECKING, Any

from advanced_alchemy.base import orm_registry
from sqlalchemy.orm import DeclarativeBase, Mapped, declarative_mixin, mapped_column
from sqlalchemy.types import String

if TYPE_CHECKING:
    from advanced_alchemy.repository.typing import ModelT


@declarative_mixin
class SlugKey:
    """Slug unique Field Model Mixin."""

    __abstract__ = True
    slug: Mapped[str] = mapped_column(String(length=100), nullable=False, unique=True, sort_order=-9)


def model_from_dict(model: ModelT, **kwargs: Any) -> ModelT:
    """Return ORM Object from Dictionary."""
    data = {column.name: kwargs.get(column.name) for column in model.__table__.columns if column.name in kwargs}
    return model(**data)  # type: ignore


class SQLQuery(DeclarativeBase):
    """Base for all SQLAlchemy custom mapped objects."""

    __allow_unmapped__ = True
    registry = orm_registry

    def to_dict(self, exclude: set[str] | None = None) -> dict[str, Any]:
        """Convert model to dictionary.

        Returns:
            dict[str, Any]: A dict representation of the model
        """
        exclude = exclude.union("_sentinel") if exclude else {"_sentinel"}
        return {field.name: getattr(self, field.name) for field in self.__table__.columns if field.name not in exclude}
