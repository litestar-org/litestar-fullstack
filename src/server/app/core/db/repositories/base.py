import asyncio
import random
import string
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Generic, List, Optional, Protocol, TypeVar, Union, overload
from uuid import UUID

from pydantic import UUID4
from sqlalchemy.engine import Result
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.sql import Select
from sqlalchemy.sql import func as sql_func
from sqlalchemy.sql import select
from sqlalchemy.sql.selectable import TypedReturnsRows

from app.core.db.models.base import DatabaseModelType, DatabaseModelWithCreatedUpdatedAtType, DatabaseModelWithSlugType
from app.utils.slugify_text import slugify

if TYPE_CHECKING:
    from sqlalchemy import Executable
    from sqlalchemy.ext.asyncio import AsyncSession

__all__ = [
    "RepositoryNotFoundException",
    "RepositoryConflictException",
    "RepositoryException",
    "ParamType",
    "RepositoryType",
    "BaseRepository",
    "SlugRepositoryMixin",
    "LimitOffset",
]

T = TypeVar("T")
ParamType = TypeVar("ParamType", bound=float | str | UUID | datetime | int)  # pylint: disable=[invalid-name]
RepositoryType = TypeVar("RepositoryType", bound="BaseRepository")  # pylint: disable=[invalid-name]
TableRowType = TypeVar("TableRowType", bound=tuple[Any, ...])  # pylint: disable=[invalid-name]


@dataclass
class LimitOffset:
    """
    Data required to add limit/offset filtering to a query.
    """

    limit: int
    """Value for `LIMIT` clause of query."""
    offset: int
    """Value for `OFFSET` clause of query."""


class RepositoryException(Exception):
    """
    Base repository exception type.
    """


class RepositoryConflictException(RepositoryException):
    """
    Wraps integrity error from database layer.
    """


class RepositoryNotFoundException(RepositoryException):
    """
    Raised when a method referencing a specific instance by identity is called and no instance with
    that identity exists.
    """


class RepositoryProtocol(Protocol[DatabaseModelType]):
    """_summary_

    Args:
        Protocol (_type_): _description_
    """

    model_type: type[DatabaseModelType]
    """
    A model that extends [`DeclarativeBase`][sqlalchemy.orm.DeclarativeBase]. Must be set by concrete subclasses.
    """
    base_error_type: type[Exception] = RepositoryException
    """
    Exception type raised when there is not a more specific error to throw.
    """
    integrity_error_type: type[Exception] = RepositoryConflictException
    """
    Exception type raised when a database layer integrity error is caught.
    """
    not_found_error_type: type[Exception] = RepositoryNotFoundException
    """
    Exception type raised on access to `scalar()`, `update()` and `delete()`
     methods when the select query returns no rows.
    Default `RepositoryNotFoundException`.
    """

    @contextmanager
    def catch_sqlalchemy_exception(self) -> Any:
        """
        Context manager that raises a custom exception chained from an original
        [`SQLAlchemyError`][sqlalchemy.exc.SQLAlchemyError].

        If [`IntegrityError`][sqlalchemy.exc.IntegrityError] is raised, we raise
        [`Base.integrity_error_type`][starlite_bedrock.repository.Base.integrity_error_type].

        Any other [`SQLAlchemyError`][sqlalchemy.exc.SQLAlchemyError] is wrapped in
        [`Base.base_error_type`][starlite_bedrock.repository.Base.base_error_type].
        """
        try:
            yield
        except IntegrityError as e:
            raise self.integrity_error_type from e
        except SQLAlchemyError as e:
            raise self.base_error_type(f"An exception occurred: {e}") from e

    @overload
    async def execute(
        self, db_session: "AsyncSession", statement: "TypedReturnsRows[TableRowType]", **kwargs: "Any"
    ) -> "Result[TableRowType]":
        ...

    @overload
    async def execute(self, db_session: "AsyncSession", statement: "Executable", **kwargs: Any) -> "Result[Any]":
        ...

    async def execute(self, db_session: "AsyncSession", statement: "Executable", **kwargs: Any) -> "Result[Any]":
        ...  # pragma: no cover

    async def commit(self, db_session: "AsyncSession") -> None:
        with self.catch_sqlalchemy_exception():
            await db_session.commit()

    async def refresh(self, db_session: "AsyncSession", db_object: "DatabaseModelType") -> None:
        with self.catch_sqlalchemy_exception():
            await db_session.refresh(db_object)

    async def flush(self, db_session: "AsyncSession") -> None:
        with self.catch_sqlalchemy_exception():
            await db_session.flush()

    async def get_by_id(
        self, db_session: "AsyncSession", id: "Union[UUID4, int]"  # pylint: disable=[redefined-builtin]
    ) -> "Optional[DatabaseModelType]":
        ...  # pragma: no cover

    async def get_one_or_none(self, db_session: "AsyncSession", statement: "Select") -> "Optional[DatabaseModelType]":
        ...  # pragma: no cover

    async def select(
        self, db_session: "AsyncSession", statement: "Select", limit_offset: LimitOffset | None = None
    ) -> Union[tuple[list[DatabaseModelType], int], list[DatabaseModelType]]:
        ...  # pragma: no cover

    async def create(self, db_session: "AsyncSession", db_object: "DatabaseModelType") -> "DatabaseModelType":
        ...  # pragma: no cover

    async def update(self, db_session: "AsyncSession", db_object: "DatabaseModelType") -> None:
        ...  # pragma: no cover

    async def delete(self, db_session: "AsyncSession", db_object: "DatabaseModelType") -> None:
        ...  # pragma: no cover


class CreatedUpdatedAtRepositoryProtocol(RepositoryProtocol, Protocol[DatabaseModelWithCreatedUpdatedAtType]):
    model: type[DatabaseModelWithCreatedUpdatedAtType]


class SlugRepositoryProtocol(RepositoryProtocol, Protocol[DatabaseModelWithSlugType]):
    model: type[DatabaseModelWithSlugType]

    async def get_by_slug(self, db_session: "AsyncSession", slug: str) -> Optional[DatabaseModelWithSlugType]:
        ...  # pragma: no cover


class BaseRepository(RepositoryProtocol, Generic[DatabaseModelType]):
    """Base SQL Alchemy repository."""

    def __init__(self) -> None:
        """
        CRUD object with default methods to create, read, update, delete (CRUD).
        """
        self.model = self.model_type

    async def get_one_or_none(self, db_session: "AsyncSession", statement: "Select") -> "Optional[DatabaseModelType]":
        statement.execution_options(populate_existing=True)
        results = await self.execute(db_session, statement)
        db_object = results.first()
        return db_object[0] if db_object else None

    async def get_by_id(
        self,
        db_session: "AsyncSession",
        id: "Union[int, UUID4]",  # pylint: disable=[redefined-builtin]
        options: "Optional[List[Any]]" = None,
    ) -> Optional[DatabaseModelType]:
        """_summary_

        Args:
            id (Union[int, UUID4]): _description_
            db (AsyncSession, optional): _description_. Defaults to AsyncSession().
            options (Optional[list], optional): _description_. Defaults to None.

        Returns:
            Optional[DatabaseModel]: _description_
        """
        options = options or []
        statement = (
            select(self.model).where(self.model.id == id).options(*options).execution_options(populate_existing=True)
        )

        return await self.get_one_or_none(db_session, statement)

    async def select(
        self,
        db_session: "AsyncSession",
        statement: Optional[Select] = None,
        limit_offset: LimitOffset | None = None,
    ) -> Union[list[DatabaseModelType], tuple[list[DatabaseModelType], int]]:
        statement = statement or select(self.model).execution_options(populate_existing=True)
        if limit_offset:
            paginated_statement = statement.offset(limit_offset.offset).limit(limit_offset.limit)
            [count, results] = await asyncio.gather(
                self.count(db_session, statement), self.execute(db_session, paginated_statement)
            )
            return [result[0] for result in results.unique().all()], count
        else:
            results = await self.execute(db_session, statement)
            return [result[0] for result in results.unique().all()]

    async def count(self, db_session: "AsyncSession", statement: "Select") -> int:
        count_statement = statement.with_only_columns(  # type: ignore[call-overload]
            [sql_func.count()],
            maintain_column_froms=True,
        ).order_by(None)
        results = await self.execute(db_session, count_statement)
        return results.scalar_one()  # type: ignore

    async def create(
        self,
        db_session: "AsyncSession",
        db_object: "DatabaseModelType",
        commit: bool = True,
    ) -> DatabaseModelType:
        db_session.add(instance=db_object)
        if commit:
            await self.commit(db_session)
        else:
            await self.flush(db_session)
        await self.refresh(db_session, db_object)
        return db_object

    async def create_many(
        self,
        db_session: "AsyncSession",
        db_objects: list[DatabaseModelType],
        commit: bool = True,
    ) -> "List[DatabaseModelType]":
        """Create Many"""
        for db_object in db_objects:
            db_session.add(instance=db_object)
        if commit:
            await self.commit(db_session)
        else:
            await self.flush(db_session)
        return db_objects

    async def update(self, db_session: "AsyncSession", db_object: "DatabaseModelType", commit: bool = True) -> None:
        db_session.add(db_object)
        if commit:
            await self.commit(db_session)
        else:
            await db_session.flush()
        await self.refresh(db_session, db_object)

    async def delete(self, db_session: "AsyncSession", db_object: "DatabaseModelType", commit: bool = True) -> None:
        with self.catch_sqlalchemy_exception():
            await db_session.delete(db_object)
            if commit:
                await self.commit(db_session)
            else:
                await self.flush(db_session)

    async def execute(self, db_session: "AsyncSession", statement: "Executable", **kwargs: "Any") -> "Result[Any]":
        """
        Execute `statement` with [`self.db`][starlite_lib.repository.Base.db].

        Parameters
        ----------
        statement : Executable
            Any SQLAlchemy executable type.
        **kwargs : Any
            Passed as kwargs to [`self.db_session.execute()`][sqlalchemy.ext.asyncio.AsyncSession.execute]

        Returns
        -------
        Result
            A set of database results.
        """
        with self.catch_sqlalchemy_exception():
            return await db_session.execute(statement, **kwargs)


class SlugRepositoryMixin(SlugRepositoryProtocol, Generic[DatabaseModelWithSlugType]):
    """Slug Repository Mixin."""

    async def get_by_slug(
        self,
        db_session: "AsyncSession",
        slug: str,
        options: "Optional[List[Any]]" = None,
    ) -> "Optional[DatabaseModelWithSlugType]":
        options = options or []
        statement = (
            select(self.model)
            .where(self.model.slug == slug)
            .options(*options)
            .execution_options(populate_existing=True)
        )

        return await self.get_one_or_none(db_session, statement)

    async def get_available_slug(
        self,
        db_session: "AsyncSession",
        value_to_slugify: str,
    ) -> str:
        slug = slugify(value_to_slugify)
        if await self._is_slug_unique(db_session, slug):
            return slug
        random_string = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))  # nosec
        return f"{slug}-{random_string}"

    async def _is_slug_unique(self, db_session: "AsyncSession", slug: str) -> bool:
        statement = select(self.model.slug).where(self.model.slug == slug)
        return await self.get_one_or_none(db_session, statement) is None
