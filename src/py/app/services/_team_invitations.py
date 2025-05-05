from __future__ import annotations

from litestar.plugins.sqlalchemy import repository, service

from app.db import models as m


class TeamInvitationService(service.SQLAlchemyAsyncRepositoryService[m.TeamInvitation]):
    """Team Invitation Service."""

    class Repo(repository.SQLAlchemyAsyncRepository[m.TeamInvitation]):
        """Team Invitation Repository."""

        model_type = m.TeamInvitation

    repository_type = Repo
