from pydantic import BaseModel as _BaseModel

from app.utils.text import camel_case

__all__ = ["BaseModel", "CamelizedBaseModel"]


class BaseModel(_BaseModel):
    """Base Settings."""

    class Config:
        """Base Settings Config."""

        case_sensitive = False
        validate_assignment = True
        orm_mode = True
        use_enum_values = True
        arbitrary_types_allowed = True


class CamelizedBaseModel(BaseModel):
    """Camelized Base pydantic schema."""

    class Config:
        """Camel Case config."""

        allow_population_by_field_name = True
        alias_generator = camel_case
