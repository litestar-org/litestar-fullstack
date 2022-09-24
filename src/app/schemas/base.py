from datetime import datetime
from enum import Enum, EnumMeta

from pydantic import BaseModel as _BaseSchema
from pydantic import SecretBytes, SecretStr

from app.utils import serializers

__all__ = ["BaseSchema", "CamelizedBaseSchema"]


class BaseSchema(_BaseSchema):
    """
    Base schema model for input deserialization and validation, and output serialization.

    Attributes
    ----------
    created : datetime
        Date/time of instance creation. Read-only attribute.
    updated: datetime
        Date/time of last instance update. Read-only attribute.
    """

    class Config:

        arbitrary_types_allowed = True
        orm_mode = True
        use_enum_values = True
        json_loads = serializers.deserialize_object
        json_dumps = serializers.serialize_object
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: serializers.convert_datetime_to_gmt,
            SecretStr: lambda secret: secret.get_secret_value() if secret else None,
            SecretBytes: lambda secret: secret.get_secret_value() if secret else None,
            Enum: lambda enum: enum.value if enum else None,
            EnumMeta: None,
        }


class CamelizedBaseSchema(BaseSchema):
    """Camelized Base pydantic schema"""

    class Config:
        allow_population_by_field_name = True
        alias_generator = serializers.convert_string_to_camel_case
