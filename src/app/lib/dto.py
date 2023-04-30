from litestar.contrib.sqlalchemy.dto import SQLAlchemyDTO
from litestar.dto.factory import DTOConfig, dto_field

__all__ = ["config", "dto_field", "DTOConfig", "SQLAlchemyDTO"]

config = DTOConfig(rename_strategy="camel")
