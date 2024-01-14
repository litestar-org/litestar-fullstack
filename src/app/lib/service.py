"""Service object implementation for SQLAlchemy.

RepositoryService object is generic on the domain model type which
should be a SQLAlchemy model.
"""

from __future__ import annotations

import contextlib
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, TypeAlias, TypeVar, overload

from advanced_alchemy.filters import (
    FilterTypes,
    LimitOffset,
)
from advanced_alchemy.repository.typing import ModelT
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService as _SQLAlchemyAsyncRepositoryService
from litestar.dto import DTOData
from litestar.pagination import OffsetPagination

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from sqlalchemy import Select
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.sql import ColumnElement


SQLAlchemyAsyncRepoServiceT = TypeVar("SQLAlchemyAsyncRepoServiceT", bound="SQLAlchemyAsyncRepositoryService")
ModelDictDTOT: TypeAlias = dict[str, Any] | ModelT | DTOData
ModelDictListDTOT: TypeAlias = list[ModelT | dict[str, Any]] | list[dict[str, Any]] | DTOData
FilterTypeT = TypeVar("FilterTypeT", bound=FilterTypes)


class SQLAlchemyAsyncRepositoryService(_SQLAlchemyAsyncRepositoryService[ModelT]):
    """Service object that operates on a repository object.

    This is the standard Advanced Alchemy Service with a few additional helper methods added:
        - Methods for formatting responses
        - Context manager for creating new services
    """

    @overload
    def to_dto(self, data: ModelT) -> ModelT:
        ...

    @overload
    def to_dto(
        self,
        data: Sequence[ModelT],
        total: int | None = None,
        *filters: FilterTypes | ColumnElement[bool],
    ) -> OffsetPagination[ModelT]:
        ...

    def to_dto(
        self,
        data: ModelT | Sequence[ModelT],
        total: int | None = None,
        *filters: FilterTypes | ColumnElement[bool],
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
        total = total or len(data)
        limit_offset = limit_offset if limit_offset is not None else LimitOffset(limit=len(data), offset=0)
        return OffsetPagination(
            items=list(data),
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
        from app.domain.config import alchemy

        if session:
            yield cls(statement=statement, session=session)
        else:
            async with alchemy.get_session() as db_session:
                yield cls(
                    statement=statement,
                    session=db_session,
                )
