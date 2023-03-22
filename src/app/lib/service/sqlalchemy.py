"""Service object implementation for SQLAlchemy.

RepositoryService object is generic on the domain model type which
should be a SQLAlchemy model.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any, Generic, TypeAlias, TypeVar

from starlite.contrib.sqlalchemy.repository import ModelT, SQLAlchemyRepository

from app.lib.db import async_session_factory
from app.lib.db.orm import model_from_dict
from app.lib.service.generic import Service

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Sequence

    from sqlalchemy import Select
    from sqlalchemy.ext.asyncio import AsyncSession
    from starlite.contrib.repository.abc import FilterTypes

SQLARepoServiceT = TypeVar("SQLARepoServiceT", bound="SQLAlchemyRepositoryService")
ModelDictT: TypeAlias = dict[str, Any] | ModelT


class SQLAlchemyRepositoryService(Service[ModelT], Generic[ModelT]):
    """Service object that operates on a repository object."""

    __item_id_ = "dma.lib.service.sqlalchemy.SQLAlchemyRepositoryService"

    repository_type: type[SQLAlchemyRepository[ModelT]]

    def __init__(self, **repo_kwargs: Any) -> None:
        """Configure the service object.

        Args:
            **repo_kwargs: passed as keyword args to repo instantiation.
        """
        self.repository = self.repository_type(**repo_kwargs)
        self.model_type = self.repository.model_type

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
        if not isinstance(data, type(self.repository.model_type)):
            data = model_from_dict(model=self.repository.model_type, data=data)  # type: ignore[arg-type, type-var]
        return await self.repository.add(data)

    async def create_many(self, data: list[ModelT | dict[str, Any]]) -> Sequence[ModelT]:  # type: ignore[override]
        """Wrap repository bulk instance creation.

        Args:
            data: Representations to be created.

        Returns:
            Representation of created instances.
        """
        data = [
            model_from_dict(model=self.repository.model_type, **datum)  # type: ignore
            if not isinstance(datum, type(self.repository.model_type))
            else datum
            for datum in data
        ]
        return await self.repository.add_many(data)  # type: ignore[arg-type]

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

    async def update(self, item_id: Any, data: ModelT | dict[str, Any]) -> ModelT:
        """Wrap repository update operation.

        Args:
            item_id: Identifier of item to be updated.
            data: Representation to be updated.

        Returns:
            Updated representation.
        """
        if not isinstance(data, type(self.repository.model_type)):
            data = model_from_dict(model=self.repository.model_type, **data)  # type: ignore[arg-type,   type-var]
        self.repository.set_id_attribute_value(item_id, data)
        return await self.repository.update(data)

    async def update_many(self, data: list[ModelT | dict[str, Any]]) -> Sequence[ModelT]:
        """Wrap repository bulk instance update.

        Args:
            data: Representations to be updated.

        Returns:
            Representation of updated instances.
        """
        data = [
            model_from_dict(model=self.repository.model_type, **datum)  # type: ignore
            if not isinstance(datum, type(self.repository.model_type))
            else datum
            for datum in data
        ]
        return await self.repository.update_many(data)  # type: ignore[arg-type]

    async def upsert(self, item_id: Any, data: ModelT | dict[str, Any]) -> ModelT:
        """Wrap repository upsert operation.

        Args:
            item_id: Identifier of the object for upsert.
            data: Representation for upsert.

        Returns:
            Updated or created representation.
        """
        self.repository.set_id_attribute_value(item_id, data)  # type: ignore[arg-type]
        if not isinstance(data, type(self.repository.model_type)):
            data = model_from_dict(model=self.repository.model_type, **data)  # type: ignore[arg-type, type-var]
        return await self.repository.upsert(data)

    async def get(self, item_id: Any, **kwargs: Any) -> ModelT:
        """Wrap repository scalar operation.

        Args:
            item_id: Identifier of instance to be retrieved.
            **kwargs: Keyword arguments for attribute based filtering.

        Returns:
            Representation of instance with identifier `item_id`.
        """
        return await self.repository.get(item_id, **kwargs)

    async def get_or_create(self, **kwargs: Any) -> tuple[ModelT, bool]:
        """Wrap repository instance creation.

        Args:
            data: Representation to be created.
            **kwargs: Keyword arguments for attribute based filtering.

        Returns:
            Representation of created instance.
        """
        return await self.repository.get_or_create(**kwargs)

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

    async def list(self, *filters: FilterTypes, **kwargs: Any) -> Sequence[ModelT]:  # noqa: A003
        """Wrap repository scalars operation.

        Args:
            *filters: Collection route filters.
            **kwargs: Keyword arguments for attribute based filtering.

        Returns:
            The list of instances retrieved from the repository.
        """
        return await self.repository.list(*filters, **kwargs)

    @classmethod
    @contextlib.asynccontextmanager
    async def new(
        cls: type[SQLARepoServiceT],
        session: AsyncSession | None = None,
        base_select: Select | None = None,
    ) -> AsyncIterator[SQLARepoServiceT]:
        """Context manager that returns instance of service object.

        Handles construction of the database session._create_select_for_model

        Returns:
            The service object instance.
        """
        if session:
            yield cls(session=session, base_select=base_select)
        else:
            async with async_session_factory() as db_session:
                yield cls(session=db_session, base_select=base_select)
