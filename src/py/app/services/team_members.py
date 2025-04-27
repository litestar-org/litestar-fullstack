from __future__ import annotations

from litestar.plugins.sqlalchemy import repository, service

from app.db import models as m


class TeamMemberService(service.SQLAlchemyAsyncRepositoryService[m.TeamMember]):
    """Team Member Service."""

    class Repo(repository.SQLAlchemyAsyncRepository[m.TeamMember]):
        """Team Member Repository."""

        model_type = m.TeamMember

    repository_type = Repo
