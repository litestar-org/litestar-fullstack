"""A generic service object implementation.

Service object is generic on the domain model type.
"""
from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeVar

from app.lib import constants
from app.lib.exceptions import NotFoundError

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
        # error: Argument of type "Type[Self@Service[T@Service]]" cannot be assigned to parameter
        #       "__value" of type "Type[Service[Any]]" in function "__setitem__"
        #   "Type[Service[T@Service]]" is incompatible with "Type[Service[Any]]"
        #   Type "Type[Self@Service[T@Service]]" cannot be assigned to type "Type[Service[Any]]"
        constants.SERVICE_OBJECT_IDENTITY_MAP[cls.__id__] = cls  # pyright:ignore

    # pylint:disable=unused-argument

    async def count(self, **kwargs: Any) -> int:
        """Count of rows returned by query.

        Args:
            **kwargs: key value pairs of filter types.

        Returns:
           A count of the collection, filtered, but ignoring pagination.
        """
        return 0

    async def create(self, data: T) -> T:
        """Create an instance of `T`.

        Args:
            data: Representation to be created.

        Returns:
            Representation of created instance.
        """
        return data

    async def create_many(self, data: list[T]) -> Sequence[T]:
        """Create many instances of `T`.

        Args:
            data: Representation to be created.

        Returns:
            Representation of created instance.
        """
        return data

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

    async def update(self, item_id: Any, data: T) -> T:
        """Update existing instance of `T` with `data`.

        Args:
            item_id: Identifier of item to be updated.
            data: Representation to be updated.

        Returns:
            Updated representation.
        """
        return data

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
        """Retrieve a representation of `T` with that is identified by `id_`.

        Args:
            item_id: Identifier of instance to be retrieved.
            **kwargs: key value pairs of filter types.

        Returns:
            Representation of instance with identifier `id_`.
        """
        raise NotFoundError

    async def get_one_or_none(self, **kwargs: Any) -> T | None:
        """Retrieve a representation of `T` with that is identified by `id_`.

        Args:
            item_id: Identifier of instance to be retrieved.
            **kwargs: key value pairs of filter types.

        Returns:
            Representation of instance with identifier `id_`.
        """

    async def delete(self, item_id: Any) -> T:
        """Delete `T` that is identified by `id_`.

        Args:
            item_id: Identifier of instance to be deleted.

        Returns:
            Representation of the deleted instance.
        """
        raise NotFoundError

    @classmethod
    @contextlib.asynccontextmanager
    async def new(cls: type[ServiceT]) -> AsyncIterator[ServiceT]:
        """Context manager that returns instance of service object.

        Returns:
            The service object instance.
        """
        yield cls()
