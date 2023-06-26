from litestar.contrib.sqlalchemy.dto import SQLAlchemyDTO

from app.domain.tags.models import Tag
from app.lib import dto

__all__ = ["TagCreateDTO", "TagDTO", "TagUpdateDTO"]


# database model


class TagDTO(SQLAlchemyDTO[Tag]):
    config = dto.config(max_nested_depth=0)


class TagCreateDTO(SQLAlchemyDTO[Tag]):
    config = dto.config(max_nested_depth=0, exclude={"id", "created_at", "updated_at", "teams"})


class TagUpdateDTO(SQLAlchemyDTO[Tag]):
    config = dto.config(max_nested_depth=0, exclude={"id", "created_at", "updated_at", "teams"}, partial=True)
