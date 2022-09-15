import uuid
from typing import Optional

from pydantic import UUID4, Field

from pyspa.schemas.base import CamelizedBaseSchema


class UploadCreate(CamelizedBaseSchema):
    """Database properties received on create"""

    object_name: Optional[str]
    object_prefix: Optional[str]


class UploadUpdate(CamelizedBaseSchema):
    """Advisor Extract properties received on update"""

    object_name: str
    object_prefix: Optional[str]


class Upload(CamelizedBaseSchema):
    """Advisor Extract properties to return from the API"""

    id: UUID4 = Field(default_factory=uuid.uuid4)
