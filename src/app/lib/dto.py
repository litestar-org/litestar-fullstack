from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, overload

from litestar.contrib.sqlalchemy.dto import SQLAlchemyDTO
from litestar.dto.factory import DTOConfig, dto_field
from litestar.dto.factory.stdlib.dataclass import DataclassDTO
from litestar.types.protocols import DataclassProtocol
from sqlalchemy.orm import DeclarativeBase

if TYPE_CHECKING:
    from collections.abc import Set

    from litestar.dto.factory.types import RenameStrategy

__all__ = ["config", "dto_field", "DTOConfig", "SQLAlchemyDTO", "DataclassDTO"]

DTOT = TypeVar("DTOT", bound=DataclassProtocol | DeclarativeBase)
DTOFactoryT = TypeVar("DTOFactoryT", bound=DataclassDTO | SQLAlchemyDTO)
SQLAlchemyModelT = TypeVar("SQLAlchemyModelT", bound=DeclarativeBase)
DataclassModelT = TypeVar("DataclassModelT", bound=DataclassProtocol)
ModelT = SQLAlchemyModelT | DataclassModelT


def config(
    exclude: Set[str] | None = None,
    rename_fields: dict[str, str] | None = None,
    rename_strategy: RenameStrategy | None = None,
    max_nested_depth: int | None = None,
    partial: bool | None = None,
) -> DTOConfig:
    """_summary_

    Returns:
        DTOConfig: Configured DTO class
    """
    default_kwargs = {"rename_strategy": "camel", "max_nested_depth": 2}
    if exclude:
        default_kwargs.update({"exclude": exclude})
    if rename_fields:
        default_kwargs.update({"rename_fields": rename_fields})
    if rename_strategy:
        default_kwargs.update({"rename_strategy": rename_strategy})
    if max_nested_depth:
        default_kwargs.update({"max_nested_depth": max_nested_depth})
    if partial:
        default_kwargs.update({"partial": partial})
    return DTOConfig(**default_kwargs)


@overload
def builder(dto: DeclarativeBase) -> DataclassDTO[DTOT]:
    ...


@overload
def builder(dto: DataclassModelT) -> SQLAlchemyDTO[DTOT]:
    ...


def builder(dto: ModelT) -> DTOFactoryT[ModelT]:
    """Construct a DTO."""
    if issubclass(dto, DeclarativeBase):
        return SQLAlchemyDTO[dto]
    return DataclassDTO[dto]
