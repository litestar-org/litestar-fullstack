import functools
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Optional, TypeAlias, TypeVar

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy import orm
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.event import listens_for
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.orm.decl_api import declarative_mixin, declared_attr
from sqlalchemy.sql import func as sql_func
from sqlalchemy.sql.expression import FunctionElement

from pyspa.db import db_types as t

if TYPE_CHECKING:
    from typing_extensions import Self

__all__ = [
    "meta",
    "mapper_registry",
    "BaseModel",
    "SlugModelMixin",
    "SoftDeleteMixin",
    "ExpiresAtMixin",
    "IntegerPrimaryKeyMixin",
]

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
"""
Templates for automated constraint name generation.
"""

meta = sa.MetaData(naming_convention=convention)
mapper_registry: orm.registry = orm.registry(metadata=meta, type_annotation_map={uuid.UUID: pg.UUID, dict: pg.JSONB})


@listens_for(orm.Session, "before_flush")
def touch_updated_timestamp(session: Session, *_: Any) -> None:
    """
    Called from SQLAlchemy's [`before_flush`][sqlalchemy.orm.SessionEvents.before_flush] event to
    bump the `updated` timestamp on modified instances.

    Parameters
    ----------
    session : Session
        The sync [`Session`][sqlalchemy.orm.Session] instance that underlies the async session.
    """
    for instance in session.dirty:
        if getattr(instance, "updated_at", None):
            setattr(instance, "updated_at", datetime.now())  # noqa: B010


class coalesce(FunctionElement):  # pylint: disable=[invalid-name]
    name = "coalesce"
    inherit_cache = True


@compiles(coalesce)  # type: ignore
def compile_coalesce(element, compiler, **kw: Any) -> str:  # type: ignore[no-untyped-def] # pylint: disable=[unused-argument]
    return f"coalesce({compiler.process(element.clauses)})"


@compiles(coalesce, "oracle")  # type: ignore
def compile_nvl(element, compiler, **kw) -> str:  # type: ignore[no-untyped-def] # pylint: disable=[unused-argument]
    if len(element.clauses) > 2:
        raise TypeError("coalesce (nvl) only supports two arguments on Oracle")
    return f"nvl({compiler.process(element.clauses)})"


class BaseModel(DeclarativeBase):
    """
    Base for all SQLAlchemy declarative models.
    """

    registry = mapper_registry
    # required in order to access columns with server defaults
    # or SQL expression defaults, subsequent to a flush, without
    # triggering an expired load
    __mapper_args__ = {"eager_defaults": True}
    id: orm.Mapped[UUID4] = sa.Column(  # type: ignore[assignment]
        t.GUID, primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    id._creation_order = 1  # type: ignore[attr-defined] # pylint: disable=[protected-access]

    def from_dict(self, **kwargs: Any) -> "Self":
        """Return ORM Object from Dictionary"""
        if self.__table__:
            for column in self.__table__.columns:
                if column.name in kwargs:
                    setattr(self, column.name, kwargs.get(column.name))
        return self

    def dict(self) -> dict[str, Any]:
        """Returns a dict representation of a model."""
        if self.__table__:
            return {field.name: getattr(self, field.name) for field in self.__table__.columns}
        return {}


@declarative_mixin
class IntegerPrimaryKeyMixin:
    """GUID Column Mixin"""

    id: orm.Mapped[int] = sa.Column(
        sa.BigInteger, sa.Identity(always=True), primary_key=True, unique=True, nullable=False
    )
    id._creation_order = 1  # type: ignore[attr-defined] # pylint: disable=[protected-access]


@declarative_mixin
class SlugModelMixin:
    slug: orm.Mapped[str] = sa.Column(sa.String(length=100), index=True, nullable=False, unique=True)
    slug._creation_order = 2  # type: ignore[attr-defined] # pylint: disable=[protected-access]


@declarative_mixin
class SoftDeleteMixin:
    is_deleted: orm.Mapped[bool] = sa.Column(sa.Boolean, index=True, nullable=False, default=False)
    is_deleted._creation_order = 999  # type: ignore[attr-defined] # pylint: disable=[protected-access]


@declarative_mixin
class CreatedUpdatedAtMixin:
    """Created At/Updated At Mixin"""

    created_at: orm.Mapped[datetime] = sa.Column(
        t.TimestampAwareDateTime(timezone=True),
        nullable=False,
        index=True,
        default=datetime.now(timezone.utc),
        server_default=sql_func.now(),
        comment="Date the record was inserted",
    )
    created_at._creation_order = 9998  # type: ignore[attr-defined] # pylint: disable=[protected-access]
    updated_at: orm.Mapped[datetime] = sa.Column(
        t.TimestampAwareDateTime(timezone=True),
        nullable=True,
        index=True,
        server_default=None,
        comment="Date the record was last modified",
    )
    updated_at._creation_order = 9998  # type: ignore[attr-defined] # pylint: disable=[protected-access]


def _get_default_expires_at(timedelta_seconds: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=timedelta_seconds)


@declarative_mixin
class ExpiresAtMixin:
    """Expires at mixin"""

    __lifetime_seconds__: int = 3600

    @declared_attr
    def expires_at(cls) -> orm.Mapped[datetime]:  # pylint: disable=[no-self-argument]
        return sa.Column(
            t.TimestampAwareDateTime(timezone=True),
            nullable=False,
            index=True,
            default=functools.partial(
                _get_default_expires_at,
                timedelta_seconds=cls.__lifetime_seconds__,
            ),
        )


def find_by_table_name(table_name: str) -> Optional["DatabaseModelType"]:
    """Return model based on class"""
    for mapper in mapper_registry.mappers:
        model: DatabaseModelType = mapper.class_  # type: ignore
        model_class_name = model.__tablename__
        if model_class_name == table_name:
            return model
    return None


DatabaseSession: TypeAlias = AsyncSession | Session
DatabaseModelType = TypeVar("DatabaseModelType", bound=BaseModel)  # pylint: disable=[invalid-name]
DatabaseModelWithSlugType = TypeVar("DatabaseModelWithSlugType", bound=SlugModelMixin)  # pylint: disable=[invalid-name]
DatabaseModelWithIntegerPrimaryKeyType = TypeVar(  # pylint: disable=[invalid-name]
    "DatabaseModelWithIntegerPrimaryKeyType", bound=IntegerPrimaryKeyMixin
)
DatabaseModelWithCreatedUpdatedAtType = TypeVar(  # pylint: disable=[invalid-name]
    "DatabaseModelWithCreatedUpdatedAtType", bound=CreatedUpdatedAtMixin
)
DatabaseModelWithExpiresAtType = TypeVar(  # pylint: disable=[invalid-name]
    "DatabaseModelWithExpiresAtType", bound=ExpiresAtMixin
)
DatabaseModelWithSoftDeleteType = TypeVar(  # pylint: disable=[invalid-name]
    "DatabaseModelWithSoftDeleteType", bound=SoftDeleteMixin
)
