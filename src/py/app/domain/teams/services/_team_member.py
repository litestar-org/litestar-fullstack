"""Team membership database service using AA 1.13 inferred default repository."""

from __future__ import annotations

from advanced_alchemy.extensions.litestar import service

from app.db import models as m


class TeamMemberService(service.SQLAlchemyAsyncRepositoryService[m.TeamMember]):
    """Team membership CRUD service."""
