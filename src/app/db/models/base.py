from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, cast

from advanced_alchemy.base import orm_registry
from sqlalchemy import (
    ColumnElement,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, declarative_mixin, mapped_column
from sqlalchemy.types import String

if TYPE_CHECKING:
    from collections.abc import Hashable

    from advanced_alchemy.repository.typing import ModelT
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.ext.asyncio.scoping import async_scoped_session


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


async def _unique(session, cls, hashfunc, queryfunc, constructor, arg, kw) -> Any:  # type: ignore[no-untyped-def]  # noqa: ANN001
    cache = getattr(session, "_unique_cache", None)
    if cache is None:
        session._unique_cache = cache = {}

    key = (cls, hashfunc(*arg, **kw))
    if key in cache:
        return cache[key]
    with session.no_autoflush:
        q = await session.query(cls)
        q = queryfunc(q, *arg, **kw)
        obj = q.first()
        if not obj:
            obj = constructor(*arg, **kw)
            session.add(obj)
    cache[key] = obj
    return obj


class UniqueMixin:
    @classmethod
    async def as_unique(
        cls,
        session: AsyncSession | async_scoped_session[AsyncSession],
        *args: Any,
        **kwargs: Any,
    ) -> Self:
        key = cls, cls.unique_hash(*args, **kwargs)
        cache = getattr(session, "_unique_cache", None)
        if cache is None:
            cache = {}
            setattr(session, "_unique_cache", cache)
        if obj := cache.get(key):
            return cast("Self", obj)

        with session.no_autoflush:
            statement = select(cls).where(cls.unique_filter(*args, **kwargs)).limit(1)
            if (obj := (await session.scalars(statement)).first()) is None:
                session.add(obj := cls(*args, **kwargs))
        cache[key] = obj
        return obj

    @classmethod
    def unique_hash(cls, *arg: Any, **kw: Any) -> Hashable:  # noqa: ARG003
        msg = "Implement this in subclass"
        raise NotImplementedError(msg)

    @classmethod
    def unique_filter(cls, *arg: Any, **kw: Any) -> ColumnElement[bool]:  # noqa: ARG003
        msg = "Implement this in subclass"
        raise NotImplementedError(msg)
