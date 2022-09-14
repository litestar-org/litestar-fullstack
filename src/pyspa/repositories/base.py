import asyncio
import random
import string
from collections import abc
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Generic, List, Optional, Protocol, Tuple, Type, TypeVar, Union, cast, overload
from uuid import UUID

from pydantic import UUID4
from sqlalchemy.engine import Result
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import InstrumentedAttribute, RelationshipProperty
from sqlalchemy.sql import Select, delete
from sqlalchemy.sql import func as sql_func
from sqlalchemy.sql import select
from sqlalchemy.sql.selectable import TypedReturnsRows

from pyspa.models.base import (
    DatabaseModelType,
    DatabaseModelWithCreatedUpdatedAtType,
    DatabaseModelWithExpiresAtType,
    DatabaseModelWithSlugType,
    DatabaseModelWithSoftDeleteType,
)
from pyspa.utils.text import slugify

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
]

T = TypeVar("T")
ParamType = TypeVar("ParamType", bound=float | str | UUID | datetime | int)  # pylint: disable=[invalid-name]
RepositoryType = TypeVar("RepositoryType", bound="BaseRepository")  # pylint: disable=[invalid-name]
TableRowType = TypeVar("TableRowType", bound=tuple[Any, ...])  # pylint: disable=[invalid-name]


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

    model: Type[DatabaseModelType]
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

    async def paginate(
        self, session: "AsyncSession", statement: "Select", limit: int = 10, offset: int = 0
    ) -> "Tuple[List[DatabaseModelType], int]":
        ...  # pragma: no cover

    @overload
    async def execute(
        self, session: "AsyncSession", statement: "TypedReturnsRows[TableRowType]", **kwargs: "Any"
    ) -> "Result[TableRowType]":
        ...

    @overload
    async def execute(self, session: "AsyncSession", statement: "Executable", **kwargs: Any) -> "Result[Any]":
        ...

    async def execute(self, session: "AsyncSession", statement: "Executable", **kwargs: Any) -> "Result[Any]":
        ...  # pragma: no cover

    async def commit(self, session: "AsyncSession") -> None:
        with self.catch_sqlalchemy_exception():
            await session.commit()

    def order_by(self, statement: "Select", ordering: "List[Tuple[List[str], bool]]") -> "Select":
        ...  # pragma: no cover

    async def get_by_id(
        self, session: "AsyncSession", id: "Union[UUID4, int]"  # pylint: disable=[redefined-builtin]
    ) -> "Optional[DatabaseModelType]":
        ...  # pragma: no cover

    async def get_one_or_none(self, session: "AsyncSession", statement: "Select") -> "Optional[DatabaseModelType]":
        ...  # pragma: no cover

    async def list(self, session: "AsyncSession", statement: "Select") -> "List[DatabaseModelType]":
        ...  # pragma: no cover

    async def create(self, session: "AsyncSession", db_object: "DatabaseModelType") -> "DatabaseModelType":
        ...  # pragma: no cover

    async def update(self, session: "AsyncSession", db_object: "DatabaseModelType") -> None:
        ...  # pragma: no cover

    async def delete(self, session: "AsyncSession", db_object: "DatabaseModelType") -> None:
        ...  # pragma: no cover


class ExpiresAtRepositoryProtocol(RepositoryProtocol, Protocol[DatabaseModelWithExpiresAtType]):
    model: Type[DatabaseModelWithExpiresAtType]

    async def delete_expired(self, session: "AsyncSession") -> None:
        ...  # pragma: no cover


class CreatedUpdatedAtRepositoryProtocol(RepositoryProtocol, Protocol[DatabaseModelWithCreatedUpdatedAtType]):
    model: Type[DatabaseModelWithCreatedUpdatedAtType]


class SlugRepositoryProtocol(RepositoryProtocol, Protocol[DatabaseModelWithSlugType]):
    model: Type[DatabaseModelWithSlugType]

    async def get_by_slug(
        self,
        session: "AsyncSession",
        slug: str,
    ) -> Optional[DatabaseModelWithSlugType]:
        ...  # pragma: no cover


class SoftDeleteRepositoryProtocol(RepositoryProtocol, Protocol[DatabaseModelWithSoftDeleteType]):
    model: Type[DatabaseModelWithSoftDeleteType]


class BaseRepository(RepositoryProtocol, Generic[DatabaseModelType]):
    """Base SQL Alchemy repository."""

    def __init__(
        self,
        model: Type[DatabaseModelType],
    ):
        """
        CRUD object with default methods to create, read, update, delete (CRUD).

        # Parameters

        * `model`: A SQLAlchemy model class
        """
        self.model = model

    async def count(self, session: "AsyncSession", statement: "Select") -> int:
        count_statement = statement.with_only_columns(  # type: ignore[call-overload]
            [sql_func.count()],
            maintain_column_froms=True,
        ).order_by(None)
        results = await self.execute(session, count_statement)
        return results.scalar_one()  # type: ignore

    async def paginate(
        self, session: "AsyncSession", statement: "Select", limit: int = 10, offset: int = 0
    ) -> Tuple[List[DatabaseModelType], int]:
        paginated_statement = statement.offset(offset).limit(limit)

        [count, results] = await asyncio.gather(
            self.count(session, statement), self.execute(session, paginated_statement)
        )

        return [result[0] for result in results.unique().all()], count

    def order_by(  # noqa: C901
        self,
        statement: "Select",
        ordering: "List[Tuple[List[str], bool]]",
    ) -> "Select":
        for (accessors, is_desc) in ordering:
            field: InstrumentedAttribute
            # Local field
            if len(accessors) == 1:
                try:
                    field = getattr(self.model, accessors[0])
                    statement = statement.order_by(field.desc() if is_desc else field.asc())
                except AttributeError:
                    pass
            # Relationship field
            else:
                valid_field = True
                model = self.model
                for accessor in accessors:
                    try:
                        field = getattr(model, accessor)
                        if isinstance(field.prop, RelationshipProperty):
                            if field.prop.lazy != "joined":
                                statement = statement.join(field)
                            model = field.prop.entity.class_
                    except AttributeError:
                        valid_field = False
                        break
                if valid_field:
                    statement = statement.order_by(field.desc() if is_desc else field.asc())
        return statement

    async def get_one_or_none(self, session: "AsyncSession", statement: "Select") -> "Optional[DatabaseModelType]":
        statement.execution_options(populate_existing=True)
        results = await self.execute(session, statement)
        db_object = results.first()
        if db_object is None:
            return None
        return cast("DatabaseModelType", db_object[0])

    async def get_by_id(
        self,
        session: "AsyncSession",
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

        return await self.get_one_or_none(session, statement)

    async def list(self, session: "AsyncSession", statement: Optional[Select] = None) -> "List[DatabaseModelType]":
        if statement is None:
            statement = select(self.model).execution_options(populate_existing=True)
        results = await self.execute(session, statement)
        return [result[0] for result in results.unique().all()]

    async def create(
        self,
        session: "AsyncSession",
        db_object: "DatabaseModelType",
        commit: bool = True,
    ) -> "DatabaseModelType":
        session.add(instance=db_object)
        if commit:
            await self.commit(session)
            await self.refresh(session, db_object)
        return db_object

    async def create_many(
        self,
        session: "AsyncSession",
        db_objects: "List[DatabaseModelType]",
        commit: bool = True,
    ) -> "List[DatabaseModelType]":
        """Create Many"""
        for db_object in db_objects:
            session.add(instance=db_object)
        if commit:
            await self.commit(session)
        return db_objects

    @staticmethod
    def update_model(model: T, data: abc.Mapping[str, Any]) -> T:
        """
        Simple helper for setting key/values from `data` as attributes on `model`.

        Parameters
        ----------
        model : T
            Model instance to be updated.
        data : Mapping[str, Any]
            Mapping of data to set as key/value pairs on `model`.

        Returns
        -------
        T
            Key/value pairs from `data` have been set on the model.
        """
        for k, v in data.items():
            setattr(model, k, v)
        return model

    async def update(self, session: "AsyncSession", db_object: "DatabaseModelType", commit: bool = True) -> None:
        session.add(db_object)
        if commit:
            await self.commit(session)
            await self.refresh(session, db_object)

    async def delete(self, session: "AsyncSession", db_object: "DatabaseModelType", commit: bool = True) -> None:
        with self.catch_sqlalchemy_exception():
            await session.delete(db_object)
            if commit:
                await self.commit(session)

    async def refresh(self, session: "AsyncSession", db_object: "DatabaseModelType") -> None:
        with self.catch_sqlalchemy_exception():
            await session.refresh(db_object)

    async def execute(self, session: "AsyncSession", statement: "Executable", **kwargs: "Any") -> "Result[Any]":
        """
        Execute `statement` with [`self.session`][starlite_lib.repository.Base.session].

        Parameters
        ----------
        statement : Executable
            Any SQLAlchemy executable type.
        **kwargs : Any
            Passed as kwargs to [`self.session.execute()`][sqlalchemy.ext.asyncio.AsyncSession.execute]

        Returns
        -------
        Result
            A set of database results.
        """
        with self.catch_sqlalchemy_exception():
            return await session.execute(statement, **kwargs)


class SlugRepositoryMixin(SlugRepositoryProtocol, Generic[DatabaseModelWithSlugType]):
    """Slug Repository Mixin."""

    async def get_by_slug(
        self,
        session: "AsyncSession",
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

        return await self.get_one_or_none(session, statement)

    async def get_available_slug(
        self,
        session: "AsyncSession",
        value_to_slugify: str,
    ) -> str:
        slug = slugify(value_to_slugify)
        if await self._is_slug_unique(session, slug):
            return slug
        random_string = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))  # nosec
        return f"{slug}-{random_string}"

    async def _is_slug_unique(
        self,
        session: "AsyncSession",
        slug: str,
    ) -> bool:
        statement = select(self.model.slug).where(self.model.slug == slug)
        return await self.get_one_or_none(session, statement) is None


class ExpiresAtMixin(ExpiresAtRepositoryProtocol, Generic[DatabaseModelWithExpiresAtType]):
    async def delete_expired(self, session: "AsyncSession") -> None:
        statement = delete(self.model).where(self.model.expires_at < datetime.now(timezone.utc))
        await self.execute(session, statement)
