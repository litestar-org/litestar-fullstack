"""A generic service object implementation.

Service object is generic on the domain model type.
"""
from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeVar, cast

from litestar.contrib.repository.exceptions import NotFoundError

from app.lib import constants

__all__ = ["Service"]


if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Sequence


T = TypeVar("T")
ServiceT = TypeVar("ServiceT", bound="Service")


class Service(Generic[T]):
    """Generic Service object."""

    __id__: ClassVar[str] = "app.lib.service.generic.Service"

    def __init_subclass__(cls, *_: Any, **__: Any) -> None:
        """Map the service object to a unique identifier.

        Important that the id is deterministic across running
        application instances, e.g., using something like `hash()` or
        `id()` won't work as those would be different on different
        instances of the running application. So we use the full import
        path to the object.
        """
        cls.__id__ = f"{cls.__module__}.{cls.__name__}"
        constants.SERVICE_OBJECT_IDENTITY_MAP[cls.__id__] = cls  # pyright:ignore

    async def count(self, **kwargs: Any) -> int:
        """Count of rows returned by query.

        Args:
            **kwargs: key value pairs of filter types.

        Returns:
           A count of the collection, filtered, but ignoring pagination.
        """
        return 0

    async def create(self, data: T | dict[str, Any]) -> T:
        """Create an instance of `T`.

        Args:
            data: Representation to be created.

        Returns:
            Representation of created instance.
        """
        return cast("T", data)

    async def create_many(self, data: list[Any] | list[dict[str, Any]]) -> Sequence[T]:
        """Create many instances of `T`.

        Args:
            data: Representation to be created.

        Returns:
            Representation of created instance.
        """
        return cast("Sequence[T]", data)

    async def update(self, item_id: Any, data: T | dict[str, Any]) -> T:
        """Update existing instance of `T` with `data`.

        Args:
            item_id: Identifier of item to be updated.
            data: Representation to be updated.

        Returns:
            Updated representation.
        """
        return cast("T", data)

    async def update_many(self, data: list[Any] | list[dict[str, Any]]) -> Sequence[T]:
        """Update many instances of `T`.

        Args:
            data: Representations to be updated.

        Returns:
            Representation of updated instance.
        """
        return cast("Sequence[T]", data)

    async def upsert(self, item_id: Any, data: T) -> T:
        """Create or update an instance of `T` with `data`.

        Args:
            item_id: Identifier of the object for upsert.
            data: Representation for upsert.

        Returns:
            Updated or created representation.
        """
        return data

    async def exists(self, **kwargs: Any) -> bool:
        """Retrieve true if at least 1 instance exists.

        Args:
            **kwargs: key value pairs of filter types.

        Returns:
            True if row exists
        """
        return False

    async def get(self, item_id: Any, **kwargs: Any) -> T:
        """Retrieve a representation of `T` with that is identified by `item_id`.

        Args:
            item_id: Identifier of instance to be retrieved.
            kwargs: Extra arguments

        Returns:
            Representation of instance with identifier `item_id`.
        """
        raise NotFoundError

    async def get_or_create(self, match_fields: list[str] | None = None, **kwargs: Any) -> tuple[T, bool]:
        """Get or create a representation of `T`.

        Args:
            match_fields: a list of keys to use to match the existing model.  When empty, all fields are matched.
            kwargs: Identifier of instance to be retrieved.

        Returns:
            Representation of instance with identifier `item_id`.
        """
        return (await self.to_model(**kwargs)), False

    async def get_one_or_none(self, **kwargs: Any) -> T | None:
        """Retrieve a representation of `T` with that is identified by `item_id`.

        Args:
            kwargs: Identifier of instance to be retrieved.

        Returns:
            Representation of instance with identifier `item_id`.
        """
        return await self.to_model(**kwargs)

    async def get_one(self, **kwargs: Any) -> T:
        """Retrieve a representation of `T` with that is identified by `item_id`.

        Args:
            kwargs: Identifier of instance to be retrieved.

        Returns:
            Representation of instance with identifier `item_id`.
        """
        raise NotFoundError

    async def delete_many(self, item_ids: list[Any]) -> Sequence[T]:
        """Delete `T` that is identified by `item_id`.

        Args:
            item_ids: Identifier of instance to be deleted.

        Returns:
            Representation of the deleted instance.
        """
        raise NotFoundError

    async def delete(self, item_id: Any) -> T:
        """Delete `T` that is identified by `item_id`.

        Args:
            item_id: Identifier of instance to be deleted.

        Returns:
            Representation of the deleted instance.
        """
        raise NotFoundError

    async def to_model(self, data: T | dict[str, Any], operation: str | None = None) -> T:
        """Parse and Convert input into a model.

        Args:
            data: Representations to be created.
            operation: Optional operation flag so that you can provide behavior based on CRUD operation

        Returns:
            Representation of created instances.
        """
        return cast("T", data)

    async def list(self, **kwargs: Any) -> Sequence[T]:
        """Return view of the collection of `T`.

        Args:
            **kwargs: Keyword arguments for filtering.

        Returns:
            The list of instances retrieved from the repository.
        """
        return []

    async def list_and_count(self, **kwargs: Any) -> tuple[Sequence[T], int]:
        """List and count records.

        Args:
            **kwargs: Keyword arguments for filtering.

        Returns:
            List of instances and count of total collection, ignoring pagination.
        """
        collection, count = await asyncio.gather(self.list(**kwargs), self.count(**kwargs))
        return collection, count

    @classmethod
    @contextlib.asynccontextmanager
    async def new(cls: type[ServiceT]) -> AsyncIterator[ServiceT]:
        """Context manager that returns instance of service object.

        Returns:
            The service object instance.
        """
        yield cls()
