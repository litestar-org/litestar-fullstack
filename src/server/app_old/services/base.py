# Standard Library
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar, Union
from uuid import UUID

from sqlalchemy import Select, select

from app import schemas
from app.core.db import repositories
from app.core.db.models.base import DatabaseModelType

RepositoryType = TypeVar("RepositoryType", bound=repositories.BaseRepository)
CreateSchemaType = TypeVar("CreateSchemaType", bound=schemas.BaseSchema)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=schemas.BaseSchema)
SchemaType = TypeVar("SchemaType", bound=schemas.BaseSchema)
ParamType = TypeVar("ParamType", bound=float | str | UUID)

if TYPE_CHECKING:
    from pydantic import UUID4
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.sql.base import ExecutableOption


@dataclass
class CollectionFilter(Generic[ParamType]):
    """
    Data required to construct a `WHERE ... IN (...)` clause.
    """

    field_name: str
    """Name of the model attribute to filter on."""
    values: list[ParamType] | None
    """Values for `IN` clause."""


class BaseRepositoryServiceException(Exception):
    """Base Data access exception type."""


class BaseRepositoryService(Generic[DatabaseModelType, RepositoryType, CreateSchemaType, UpdateSchemaType]):
    """Base class for all Database CRUD operations.

    This class is used to provide a common interface for all CRUD operations.
    """

    model_type: type[DatabaseModelType]
    repository_type: type[RepositoryType]

    def __init__(self, default_options: Optional[list["ExecutableOption"]] = None) -> None:
        """
        CRUD object with default methods to create, read, update, delete (CRUD).

        # Parameters

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """

        self.repository = self.repository_type()
        self.model = self.model_type
        self.default_options = default_options if default_options else []

    async def get_by_id(
        self, db_session: "AsyncSession", id: "UUID4", options: Optional[list["Any"]] = None
    ) -> Optional[DatabaseModelType]:
        """
        Obtain model instance by `identifier`.

        Args:
            id: The identifier of the model instance.
            db_session:   The database session.
        Returns:
            Returns `None` on unsuccessful search`.
        """
        options = options if options else self.default_options
        return await self.repository.get_by_id(db_session, id, options)

    async def get_one_or_none(
        self, db_session: "AsyncSession", *args: Any, options: Optional[list[Any]] = None, **kwargs: Any
    ) -> Optional[DatabaseModelType]:
        """
        Obtain a list of model instances

        List starts at offset `skip` and contains a
        maximum of `limit` number of elements.

        Args:
            skip: The offset of the list.
            limit: The maximum number of elements in the list.
            db_session:   The database session.
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
        )
        return await self.repository.get_one_or_none(db_session, statement)

    async def get(
        self,
        db_session: "AsyncSession",
        limit_offset: repositories.LimitOffset | None = None,
        options: Optional[list["ExecutableOption"]] = None,
        **kwargs: Any,
    ) -> Union[list[DatabaseModelType], tuple[list[DatabaseModelType], int]]:
        """
        Obtain a list of model instances

        List starts at offset `skip` and contains a
        maximum of `limit` number of elements.

        Args:
            skip: The offset of the list.
            limit: The maximum number of elements in the list.
            db_session:   The database session.
        Returns:
            Returns a paginated response
        """
        options = options if options else self.default_options
        statement = select(self.model).options(*options).execution_options(populate_existing=True)
        statement = self._filter_select_by_kwargs(statement, **kwargs)
        if limit_offset:
            results, count = await self.repository.select(db_session, statement, limit_offset=limit_offset)
            return results, count
        results = await self.repository.select(db_session, statement)
        return results

    async def create(self, db_session: "AsyncSession", obj_in: CreateSchemaType) -> DatabaseModelType:
        """Create an instance of the model and insert it into the database.

        Args:
            db_session:   The database session.
            obj_in: The object to create.

        Returns:
            The created object.

        """
        obj_in_data = obj_in.dict(exclude_unset=True, by_alias=False, exclude_none=True)
        db_obj = self.model(**obj_in_data)
        await self.repository.create(db_session, db_obj)
        return db_obj

    async def update(
        self, db_session: "AsyncSession", db_obj: DatabaseModelType, obj_in: Union[UpdateSchemaType, dict[str, Any]]
    ) -> DatabaseModelType:
        """
        Update model instance `db_obj` with fields and values specified by `obj_in`.

        Args:
            db_session:   The database session.
            db_obj: The object to update.
            obj_in: The object to update with.
        Returns:
            The updated object.

        """
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.dict(exclude_unset=True, by_alias=False)
        for field in db_obj.dict():
            if field in update_data:
                setattr(db_obj, field, update_data.get(field))
        await self.repository.update(db_session, db_obj)
        return db_obj

    async def delete(self, db_session: "AsyncSession", id: "UUID4") -> Optional[DatabaseModelType]:
        """Delete model instance by `identifier`.

        Args:
            db_session:   The database session.
            id: The identifier of the model instance.
        Returns:
            The deleted object.
        """
        db_obj = await self.repository.get_by_id(db_session, id)
        if db_obj:
            await self.repository.delete(db_session, db_obj)
        return db_obj or None

    def _filter_select_by_kwargs(self, statement: "Select", **kwargs: Any) -> "Select":
        """
        Add a where clause to `self.select` for each key/value pair in `**kwargs` where key should
        be an attribute of `model_type` and value is used for an equality test.

        Parameters
        ----------
        **kwargs : Any
            Keys should be attributes of `model_type`.
        """
        for k, v in kwargs.items():
            statement.where(getattr(self.model, k) == v)
        return statement
