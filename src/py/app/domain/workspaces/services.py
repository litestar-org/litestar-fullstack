from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from app.db import models as m
from app.lib.service import AutoSlugServiceMixin


class WorkspaceService(AutoSlugServiceMixin[m.Workspace], service.SQLAlchemyAsyncRepositoryService[m.Workspace]):
    """Handles CRUD operations on Workspace resources."""

    class Repo(repository.SQLAlchemyAsyncSlugRepository[m.Workspace]):
        """Workspace Repository."""

        model_type = m.Workspace

    repository_type = Repo
    match_fields = ["name"]


class TaskService(service.SQLAlchemyAsyncRepositoryService[m.Task]):
    """Handles CRUD operations on Task resources."""

    class Repo(repository.SQLAlchemyAsyncRepository[m.Task]):
        """Task Repository."""

        model_type = m.Task

    repository_type = Repo
