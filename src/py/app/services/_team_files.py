from __future__ import annotations

from litestar.plugins.sqlalchemy import repository, service

from app.db import models as m


class TeamFileService(service.SQLAlchemyAsyncRepositoryService[m.TeamFile]):
    """Team File Service."""

    class Repo(repository.SQLAlchemyAsyncRepository[m.TeamFile]):
        """Team Files Repository."""

        model_type = m.TeamFile

    repository_type = Repo
