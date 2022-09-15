# Standard Library
from enum import Enum
from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar, Union

from pydantic.generics import GenericModel
from sqlalchemy import select

from pyspa import models, repositories, schemas

ModelType = TypeVar("ModelType", bound=models.BaseModel)
RepositoryType = TypeVar("RepositoryType", bound=repositories.BaseRepository)
CreateSchemaType = TypeVar("CreateSchemaType", bound=schemas.BaseSchema)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=schemas.BaseSchema)
SchemaType = TypeVar("SchemaType", bound=schemas.BaseSchema)

if TYPE_CHECKING:
    from pydantic import UUID4
    from sqlalchemy.ext.asyncio import AsyncSession


class TableSortOrder(str, Enum):
    ASCENDING = "asc"
    DESCENDING = "desc"


class TablePageSize(str, Enum):
    TEN = 10
    TWENTY_FIVE = 25
    FIFTY = 50


class TotaledResults(GenericModel, Generic[SchemaType]):
    """Provides count and result of result set"""

    count: int
    results: list[SchemaType]


class PaginatedResults(GenericModel, Generic[SchemaType]):
    """Provides count, result, and page information of result set"""

    count: int
    limit: int
    skip: int
    results: list[SchemaType]


class DataAccessServiceException(Exception):
    """Base Data access exception type."""


class DataAccessService(Generic[ModelType, RepositoryType, CreateSchemaType, UpdateSchemaType]):
    """Base class for all Database CRUD operations.

    This class is used to provide a common interface for all CRUD operations.
    """

    def __init__(
        self,
        model: type[ModelType],
        repository: type[RepositoryType],
        default_options: Optional[list[Any]] = None,
    ) -> None:
        """
        CRUD object with default methods to create, read, update, delete (CRUD).

        # Parameters

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model
        self.repository = repository(model=model)
        self.default_options = default_options if default_options else []

    async def get_by_id(
        self, db: "AsyncSession", id: "UUID4", options: Optional[list[Any]] = None
    ) -> Optional[ModelType]:
        """
        Obtain model instance by `identifier`.

        Args:
            id: The identifier of the model instance.
            db: The database session.
        Returns:
            Returns `None` on unsuccessful search`.
        """
        options = options if options else self.default_options
        db_obj = await self.repository.get_by_id(db, id, options)
        return db_obj or None

    async def get(
        self, db: "AsyncSession", *args: Any, options: Optional[list[Any]] = None, **kwargs: Any
    ) -> Optional[SchemaType]:
        """
        Obtain a list of model instances

        List starts at offset `skip` and contains a
        maximum of `limit` number of elements.

        Args:
            skip: The offset of the list.
            limit: The maximum number of elements in the list.
            db: The database session.
        Returns:
            Returns a paginated response
        """
        options = options if options else self.default_options
        statement = (
            select(self.model)
            .filter(*args)
            .filter_by(**kwargs)
            .options(*options)
            .execution_options(populate_existing=True)
        )  # this is important!
        db_obj = await self.repository.get_one_or_none(db, statement)
        return db_obj or None

    async def get_multi(
        self,
        db: "AsyncSession",
        *args: Any,
        skip: int = 0,
        limit: int = 100,
        options: Optional[list[Any]] = None,
        **kwargs: Any,
    ) -> tuple[list[ModelType], int]:
        """
        Obtain a list of model instances

        List starts at offset `skip` and contains a
        maximum of `limit` number of elements.

        Args:
            skip: The offset of the list.
            limit: The maximum number of elements in the list.
            db: The database session.
        Returns:
            Returns a paginated response
        """
        options = options if options else self.default_options

        sort = kwargs.pop("sort", None)
        order = kwargs.pop("order", None)
        sort_by = sort if sort else TableSortOrder.DESCENDING
        order_by = self.model.id  # default to PK
        if order and getattr(self.model, order, None):
            order_by = getattr(self.model, order, order_by)
        if sort_by == TableSortOrder.ASCENDING:
            order_by = order_by.asc()  # type: ignore[assignment]
        elif sort_by == TableSortOrder.DESCENDING:
            order_by = order_by.desc()  # type: ignore[assignment]
        statement = (
            select(self.model)
            .filter(*args)
            .filter_by(**kwargs)
            .offset(skip)
            .limit(limit)
            .order_by(order_by)
            .options(*options)
            .execution_options(populate_existing=True)
        )  # this is important!
        results, count = await self.repository.paginate(db, statement, limit, skip)
        return results, count

    async def list(
        self, db: "AsyncSession", *args: Any, options: Optional[list[Any]] = None, **kwargs: Any
    ) -> list[ModelType]:
        """
        Obtain a list of model instances

        Returns all elements as a list.  No pagination

        Args:
            skip: The offset of the list.
            limit: The maximum number of elements in the list.
            db: The database session.
        Returns:
            Returns a paginated response
        """
        options = options if options else self.default_options

        statement = (
            select(self.model)
            .filter(*args)
            .filter_by(**kwargs)
            .options(*options)
            .execution_options(populate_existing=True)
        )  # this is important!
        results = await self.repository.list(db, statement)
        return results

    async def create(self, db: "AsyncSession", obj_in: CreateSchemaType) -> ModelType:
        """Create an instance of the model and insert it into the database.

        Args:
            db: The database session.
            obj_in: The object to create.

        Returns:
            The created object.

        """
        obj_in_data = obj_in.dict(exclude_unset=True, by_alias=False, exclude_none=True)
        db_obj = self.model(**obj_in_data)
        await self.repository.create(db, db_obj)
        return db_obj

    async def update(
        self, db: "AsyncSession", db_obj: ModelType, obj_in: Union[UpdateSchemaType, dict[str, Any]]
    ) -> ModelType:
        """
        Update model instance `db_obj` with fields and values specified by `obj_in`.

        Args:
            db: The database session.
            db_obj: The object to update.
            obj_in: The object to update with.
        Returns:
            The updated object.

        """
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.dict(exclude_unset=True, by_alias=False)
        for field in db_obj.dict():
            if field in update_data:
                setattr(db_obj, field, update_data.get(field))
        await self.repository.update(db, db_obj)
        return db_obj

    async def remove(self, db: "AsyncSession", id: int) -> Optional[ModelType]:
        """Delete model instance by `identifier`.

        Args:
            db: The database session.
            id: The identifier of the model instance.
        Returns:
            The deleted object.
        """
        db_obj = await self.repository.get_by_id(db, id)
        if db_obj:
            await self.repository.delete(db, db_obj)
        return db_obj or None
