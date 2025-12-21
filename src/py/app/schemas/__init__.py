"""Base schema utilities.

Domain-specific schemas should be imported from their respective domain modules:
- app.domain.accounts.schemas
- app.domain.teams.schemas
- app.domain.tags.schemas
- app.domain.system.schemas
"""

from app.schemas.base import BaseSchema, BaseStruct, CamelizedBaseSchema, CamelizedBaseStruct, Message

__all__ = (
    "BaseSchema",
    "BaseStruct",
    "CamelizedBaseSchema",
    "CamelizedBaseStruct",
    "Message",
)
