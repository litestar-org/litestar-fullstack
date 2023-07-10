from __future__ import annotations

from typing import Any

from app.lib.service.sqlalchemy import SQLAlchemyAsyncRepository
from app.lib.service.sqlalchemy import SQLAlchemyAsyncRepositoryService

from .models import CPE

__all__ = ['CpeService', "CpeRepository"]


class CpeRepository(SQLAlchemyAsyncRepository[CPE]):
    """CPE Sqlalchemy Repository"""

    model_type = CPE


class CpeService(SQLAlchemyAsyncRepositoryService[CPE]):

    repository_type = CpeRepository

    def __init__(self, **repo_kwargs: Any) -> None:
        self.repository: CpeRepository = self.repository_type(**repo_kwargs)
        self.model_type = self.repository.model_type
