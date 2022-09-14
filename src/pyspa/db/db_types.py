from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Literal, Optional, cast
from uuid import UUID

from pydantic import UUID4, EmailStr, SecretStr
from sqlalchemy import JSON, TIMESTAMP, Column, String, Unicode, type_coerce
from sqlalchemy.dialects.postgresql import BYTEA, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import ColumnProperty
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql import func as sql_func
from sqlalchemy.types import CHAR, TypeDecorator, TypeEngine

if TYPE_CHECKING:
    from pydantic import BaseModel as BaseSchema
    from sqlalchemy import ColumnOperators
    from sqlalchemy.engine import Dialect


def inspect_type(mixed: Any) -> TypeEngine:
    if isinstance(mixed, InstrumentedAttribute):
        return cast("TypeEngine", mixed.property.columns[0].type)
    elif isinstance(mixed, ColumnProperty):
        return mixed.columns[0].type
    elif isinstance(mixed, Column):
        return mixed.type
    raise ValueError(f"{mixed} is not a valid type")


def is_case_insensitive(mixed: Any) -> bool:
    """Case Insensitive check

    Return try is the columns is configured to compare with a Case Insensitive Comparator



    Args:
        mixed (Any): _description_

    Returns:
        bool: true if using CaseInsensitiveComparator
    """
    try:
        return isinstance(inspect_type(mixed).Comparator, CaseInsensitiveComparator)
    except AttributeError:
        try:
            return issubclass(
                inspect_type(mixed).comparator_factory,  # type: ignore[arg-type]
                CaseInsensitiveComparator,
            )
        except AttributeError:
            return False


class CaseInsensitiveComparator(Unicode.Comparator):
    """Case Insensitive Comparator

    SQL String column comparer that ignore case.

    Args:
        Unicode (_type_): _description_

    Returns:
        _type_: _description_
    """

    @classmethod
    def lowercase_arg(cls, func: Any) -> Any:
        """Lowercase Arguments in operation

        Args:
            func (Any): _description_

        Returns:
            Any: _description_
        """

        def operation(self: Any, other: Any, **kwargs: Any) -> Any:
            operator = getattr(Unicode.Comparator, func)
            if other is None:
                return operator(self, other, **kwargs)
            if not is_case_insensitive(other):
                other = sql_func.lower(other)
            return operator(self, other, **kwargs)

        return operation(cls, func)

    def in_(self, other: Any) -> "ColumnOperators":
        if isinstance(other, (list, tuple)):
            other = map(sql_func.lower, other)
        return Unicode.Comparator.in_(self, other)

    def not_in(self, other: Any) -> "ColumnOperators":
        if isinstance(other, (list, tuple)):
            other = map(sql_func.lower, other)
        return Unicode.Comparator.not_in(self, other)


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.
    """

    class UUIDChar(CHAR):
        python_type = UUID4

    impl = UUIDChar
    cache_ok = True

    def load_dialect_impl(self, dialect: "Dialect") -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value: Any, dialect: "Dialect") -> Optional[str]:
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, UUID):
                return "%.32x" % UUID(value).int  # pylint: disable=[consider-using-f-string]
            else:
                return "%.32x" % value.int  # pylint: disable=[consider-using-f-string]

    def process_result_value(self, value: Any, dialect: "Dialect") -> Any:
        if value is None:
            return value
        else:
            if not isinstance(value, UUID):
                value = UUID(value)
            return value

    @property
    def python_type(self) -> type[UUID4]:
        return self.impl.python_type


class TimestampAwareDateTime(TypeDecorator):
    """
    MySQL and SQLite will always return naive-Python datetimes.

    We store everything as UTC, but we want to have
    only offset-aware Python datetimes, even with MySQL and SQLite.
    """

    class DateTimeType(TIMESTAMP):
        python_type = datetime

    impl = DateTimeType
    cache_ok = True

    def process_result_value(self, value: Optional[datetime], dialect: "Dialect") -> Optional[datetime]:
        if value is not None and dialect.name not in {"postgresql", "oracle"}:
            return value.replace(tzinfo=timezone.utc)
        return value

    @property
    def python_type(self) -> type[datetime]:
        return self.impl.python_type


class EmailString(TypeDecorator):
    """
    Email string validator
    """

    class EmailType(Unicode):
        python_type = EmailStr

    impl = EmailType
    comparator_factory = CaseInsensitiveComparator
    cache_ok = True

    def __init__(self, *args: Any, length: int = 255, **kwargs: Any) -> None:
        kwargs["length"] = length
        super().__init__(*args, **kwargs)

    def process_bind_param(self, value: Optional[str | EmailStr], dialect: "Dialect") -> Any | None:
        if value is not None:
            return value.lower()
        return value

    @property
    def python_type(self) -> type[EmailStr]:
        return self.impl.python_type


class JsonObject(TypeDecorator):
    """Platform-independent JSON type.

    Uses JSONB type for postgres, otherwise uses generic JSON
    """

    class JSONType(String):
        python_type = dict[str, Any]

    impl = JSONType
    cache_ok = True

    def load_dialect_impl(self, dialect: "Dialect") -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())  # type: ignore[no-untyped-call]
        else:
            return dialect.type_descriptor(JSON())

    @property
    def python_type(self) -> type[dict[str, Any]]:
        return self.impl.python_type


class PydanticType(TypeDecorator):
    """Pydantic type.
    SAVING:
    - Uses SQLAlchemy JSON type under the hood.
    - Accepts the pydantic model and converts it to a dict on save.
    - SQLAlchemy engine JSON-encodes the dict to a string.
    RETRIEVING:
    - Pulls the string from the database.
    - SQLAlchemy engine JSON-decodes the string to a dict.
    - Uses the dict to create a pydantic model.
    """

    impl = JsonObject
    cache_ok = True

    def __init__(self, pydantic_type: "BaseSchema"):
        super().__init__()
        self.pydantic_type = pydantic_type

    def process_bind_param(self, value: Any, dialect: "Dialect") -> Any:
        return value.dict() if value else None

    def process_result_value(self, value: Any, dialect: "Dialect") -> Any:
        return self.pydantic_type.parse_obj(value) if value else None


class EncryptedString(TypeDecorator):
    """Encrypted String

    Configurable encrypted string field for SQL Alchemy
    Args:
        TypeDecorator (_type_): _description_

    Raises:
        NotImplementedError: Unsupported backend

    Returns:
        _type_: _description_
    """

    impl = BYTEA

    cache_ok = True

    def __init__(self, passphrase: SecretStr | str, backend: Literal["pgcrypto", "tink"] = "pgcrypto") -> None:
        super().__init__()
        self.passphrase = passphrase
        self.backend = backend

    def bind_expression(self, bindparam: Any) -> Any:
        # convert the bind's type from EncryptedString to
        # String, so that it's passed to postgres as is without
        # a dbapi.Binary wrapper
        bindparam = type_coerce(bindparam, String)
        if self.backend == "pgcrypto":
            return sql_func.pgp_sym_encrypt(bindparam, self.passphrase)
        if self.backend == "tink":
            raise NotImplementedError

    def column_expression(self, column: Any) -> Any:
        if self.backend == "pgcrypto":
            return sql_func.pgp_sym_encrypt(column, self.passphrase)
        if self.backend == "tink":
            raise NotImplementedError
