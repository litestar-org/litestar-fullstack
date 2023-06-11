from litestar.contrib.sqlalchemy.dto import SQLAlchemyDTO

from app.domain.tags.models import Tag
from app.lib import dto

# database model


class TagDTO(SQLAlchemyDTO[Tag]):
    config = dto.config(max_nested_depth=0)


class TagCreateDTO(SQLAlchemyDTO[Tag]):
    config = dto.config(max_nested_depth=0, exclude={"id", "created", "updated", "teams"})


class TagUpdateDTO(SQLAlchemyDTO[Tag]):
    config = dto.config(max_nested_depth=0, exclude={"id", "created", "updated", "teams"}, partial=True)
