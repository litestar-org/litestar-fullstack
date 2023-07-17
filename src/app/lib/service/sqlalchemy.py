"""Service object implementation for SQLAlchemy.

RepositoryService object is generic on the domain model type which
should be a SQLAlchemy model.
"""

from __future__ import annotations

import contextlib
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Generic, TypeAlias, TypeVar, cast, overload

from litestar.contrib.repository.filters import (
    FilterTypes,
    LimitOffset,
)
from litestar.contrib.sqlalchemy.repository import ModelT, SQLAlchemyAsyncRepository
from litestar.pagination import OffsetPagination
from pydantic.type_adapter import TypeAdapter

from app.lib.db import async_session_factory
from app.lib.db.orm import model_from_dict

from .generic import Service

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from pydantic import BaseModel
    from sqlalchemy import Select
    from sqlalchemy.ext.asyncio import AsyncSession

__all__ = ["SQLAlchemyAsyncRepositoryService"]

SQLAlchemyAsyncRepoServiceT = TypeVar("SQLAlchemyAsyncRepoServiceT", bound="SQLAlchemyAsyncRepositoryService")
ModelDictT: TypeAlias = dict[str, Any] | ModelT
ModelDictListT: TypeAlias = list[ModelT | dict[str, Any]] | list[dict[str, Any]]
ModelDTOT = TypeVar("ModelDTOT", bound="BaseModel")
FilterTypeT = TypeVar("FilterTypeT", bound=FilterTypes)


class SQLAlchemyAsyncRepositoryService(Service[ModelT], Generic[ModelT]):
    """Service object that operates on a repository object."""

    __item_id_ = "app.lib.service.sqlalchemy.SQLAlchemyAsyncRepositoryService"
    repository_type: type[SQLAlchemyAsyncRepository[ModelT]]
    match_fields: list[str] | None = None

    def __init__(self, **repo_kwargs: Any) -> None:
        """Configure the service object.

        Args:
            **repo_kwargs: passed as keyword args to repo instantiation.
        """
        self.repository = self.repository_type(**repo_kwargs)

    async def count(self, *filters: FilterTypes, **kwargs: Any) -> int:
        """Count of records returned by query.

        Args:
            *filters: arguments for filtering.
            **kwargs: key value pairs of filter types.

        Returns:
           A count of the collection, filtered, but ignoring pagination.
        """
        return await self.repository.count(*filters, **kwargs)

    async def create(self, data: ModelT | dict[str, Any]) -> ModelT:
        """Wrap repository instance creation.

        Args:
            data: Representation to be created.

        Returns:
            Representation of created instance.
        """
        data = await self.to_model(data, "create")
        return await self.repository.add(data)

    async def create_many(
        self, data: list[ModelT | dict[str, Any]] | list[dict[str, Any]] | list[ModelT]
    ) -> Sequence[ModelT]:
        """Wrap repository bulk instance creation.

        Args:
            data: Representations to be created.

        Returns:
            Representation of created instances.
        """
        data = [(await self.to_model(datum, "create")) for datum in data]
        return await self.repository.add_many(data)

    async def update(self, item_id: Any, data: ModelT | dict[str, Any]) -> ModelT:
        """Wrap repository update operation.

        Args:
            item_id: Identifier of item to be updated.
            data: Representation to be updated.

        Returns:
            Updated representation.
        """
        data = await self.to_model(data, "update")
        data = self.repository.set_id_attribute_value(item_id, data)
        return await self.repository.update(data)

    async def update_many(
        self, data: list[ModelT | dict[str, Any]] | list[dict[str, Any]] | list[ModelT]
    ) -> Sequence[ModelT]:
        """Wrap repository bulk instance update.

        Args:
            data: Representations to be updated.

        Returns:
            Representation of updated instances.
        """
        data = [(await self.to_model(datum, "update")) for datum in data]
        return await self.repository.update_many(data)

    async def upsert(self, item_id: Any, data: ModelT | dict[str, Any]) -> ModelT:
        """Wrap repository upsert operation.

        Args:
            item_id: Identifier of the object for upsert.
            data: Representation for upsert.

        Returns:
            Updated or created representation.
        """
        data = await self.to_model(data, "upsert")
        self.repository.set_id_attribute_value(item_id, data)
        return await self.repository.upsert(data)

    async def exists(self, **kwargs: Any) -> bool:
        """Wrap repository exists operation.

        Args:
            **kwargs: Keyword arguments for attribute based filtering.

        Returns:
            Representation of instance with identifier `item_id`.
        """
        return bool((await self.repository.count(**kwargs)) > 0)

    async def get(self, item_id: Any, **kwargs: Any) -> ModelT:
        """Wrap repository scalar operation.

        Args:
            item_id: Identifier of instance to be retrieved.
            **kwargs: Keyword arguments for attribute based filtering.

        Returns:
            Representation of instance with identifier `item_id`.
        """
        return await self.repository.get(item_id, **kwargs)

    async def get_or_create(self, match_fields: list[str] | None = None, **kwargs: Any) -> tuple[ModelT, bool]:
        """Wrap repository instance creation.

        Args:
            match_fields: a list of keys to use to match the existing model.  When empty, all fields are matched.
            **kwargs: Keyword arguments for attribute based filtering.

        Returns:
            Representation of created instance.
        """
        match_fields = match_fields if match_fields else self.match_fields
        validated_model = await self.to_model(kwargs, "create")
        # todo: submit PR with repo enhancements
        return await self.repository.get_or_create(**validated_model.to_dict())

    async def get_one(self, **kwargs: Any) -> ModelT:
        """Wrap repository scalar operation.

        Args:
            **kwargs: Keyword arguments for attribute based filtering.

        Returns:
            Representation of instance with identifier `item_id`.
        """
        return await self.repository.get_one(**kwargs)

    async def get_one_or_none(self, **kwargs: Any) -> ModelT | None:
        """Wrap repository scalar operation.

        Args:
            **kwargs: Keyword arguments for attribute based filtering.

        Returns:
            Representation of instance with identifier `item_id`.
        """
        return await self.repository.get_one_or_none(**kwargs)

    async def delete(self, item_id: Any) -> ModelT:
        """Wrap repository delete operation.

        Args:
            item_id: Identifier of instance to be deleted.

        Returns:
            Representation of the deleted instance.
        """
        return await self.repository.delete(item_id)

    async def delete_many(self, item_ids: list[Any]) -> Sequence[ModelT]:
        """Wrap repository bulk instance deletion.

        Args:
            item_ids: IDs to be removed.

        Returns:
            Representation of removed instances.
        """
        return await self.repository.delete_many(item_ids)

    async def to_model(self, data: ModelT | dict[str, Any], operation: str | None = None) -> ModelT:
        """Parse and Convert input into a model.

        Args:
            data: Representations to be created.
            operation: Optional operation flag so that you can provide behavior based on CRUD operation
        Returns:
            Representation of created instances.
        """
        if isinstance(data, dict):
            return model_from_dict(model=self.repository.model_type, **data)  # type: ignore[type-var,return-value]
        return data

    async def list_and_count(
        self,
        *filters: FilterTypes,
        **kwargs: Any,
    ) -> tuple[Sequence[ModelT], int]:
        """List of records and total count returned by query.

        Args:
            *filters: arguments for filtering.
            **kwargs: Keyword arguments for filtering.

        Returns:
            List of instances and count of total collection, ignoring pagination.
        """
        return await self.repository.list_and_count(*filters, **kwargs)

    @overload
    def to_dto(self, data: ModelT) -> ModelT:
        ...

    @overload
    def to_dto(
        self, data: Sequence[ModelT], total: int | None = None, *filters: FilterTypes
    ) -> OffsetPagination[ModelT]:
        ...

    def to_dto(
        self, data: ModelT | Sequence[ModelT], total: int | None = None, *filters: FilterTypes
    ) -> ModelT | OffsetPagination[ModelT]:
        """Convert the object to a format expected by the DTO handler

        Args:
            data: The return from one of the service calls.
            total: the total number of rows in the data
            *filters: Collection route filters.

        Returns:
            The list of instances retrieved from the repository.
        """
        if not isinstance(data, Sequence | list):
            return data
        limit_offset = self.find_filter(LimitOffset, *filters)
        total = total if total else len(data)
        limit_offset = limit_offset if limit_offset is not None else LimitOffset(limit=len(data), offset=0)
        return OffsetPagination(
            items=list(data),
            limit=limit_offset.limit,
            offset=limit_offset.offset,
            total=total,
        )

    @overload
    def to_schema(self, dto: type[ModelDTOT], data: ModelT) -> ModelDTOT:
        ...

    @overload
    def to_schema(
        self,
        dto: type[ModelDTOT],
        data: Sequence[ModelT],
        total: int | None = None,
        *filters: FilterTypes,
    ) -> OffsetPagination[ModelDTOT]:
        ...

    def to_schema(
        self,
        dto: type[ModelDTOT],
        data: ModelT | Sequence[ModelT],
        total: int | None = None,
        *filters: FilterTypes,
    ) -> ModelDTOT | OffsetPagination[ModelDTOT]:
        """Convert the object to a response schema.

        Args:
            dto: Collection route filters.
            data: The return from one of the service calls.
            total: the total number of rows in the data
            *filters: Collection route filters.

        Returns:
            The list of instances retrieved from the repository.
        """
        if not isinstance(data, Sequence | list):
            return TypeAdapter(dto).validate_python(data)
        limit_offset = self.find_filter(LimitOffset, *filters)
        total = total if total else len(data)
        limit_offset = limit_offset if limit_offset is not None else LimitOffset(limit=len(data), offset=0)
        return OffsetPagination[dto](  # type: ignore[valid-type]
            items=TypeAdapter(list[dto]).validate_python(data),  # type: ignore[valid-type]
            limit=limit_offset.limit,
            offset=limit_offset.offset,
            total=total,
        )

    @classmethod
    @contextlib.asynccontextmanager
    async def new(
        cls: type[SQLAlchemyAsyncRepoServiceT],
        session: AsyncSession | None = None,
        statement: Select | None = None,
    ) -> AsyncIterator[SQLAlchemyAsyncRepoServiceT]:
        """Context manager that returns instance of service object.

        Handles construction of the database session._create_select_for_model

        Returns:
            The service object instance.
        """
        if session:
            yield cls(statement=statement, session=session)
        else:
            async with async_session_factory() as db_session:
                yield cls(
                    statement=statement,
                    session=db_session,
                )

    @staticmethod
    def find_filter(filter_type: type[FilterTypeT], *filters: FilterTypes) -> FilterTypeT | None:
        """Get the filter specified by filter type from the filters.

        Args:
            filter_type: The type of filter to find.
            *filters: filter types to apply to the query

        Returns:
            The match filter instance or None
        """
        for filter_ in filters:
            if isinstance(filter_, filter_type):
                return cast("FilterTypeT | None", filter_)
        return None

    async def list(self, *filters: FilterTypes, **kwargs: Any) -> Sequence[ModelT]:
        """Wrap repository scalars operation.

        Args:
            *filters: Collection route filters.
            **kwargs: Keyword arguments for attribute based filtering.

        Returns:
            The list of instances retrieved from the repository.
        """
        return await self.repository.list(*filters, **kwargs)
