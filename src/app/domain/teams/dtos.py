from dataclasses import dataclass, field

from litestar.contrib.sqlalchemy.dto import SQLAlchemyDTO
from litestar.dto import DataclassDTO

from app.domain.teams.models import Team
from app.lib import dto

__all__ = ["TeamCreate", "TeamCreateDTO", "TeamDTO", "TeamUpdate", "TeamUpdateDTO"]


# database model


class TeamDTO(SQLAlchemyDTO[Team]):
    config = dto.config(
        exclude={
            "members.team",
            "members.user",
            "members.created_at",
            "members.updated_at",
            "members.id",
            "members.user_name",
            "members.user_email",
            "invitations",
            "pending_invitations",
        },
        max_nested_depth=1,
    )


@dataclass
class TeamCreate:
    name: str
    description: str | None = None
    tags: list[str] = field(default_factory=list)


class TeamCreateDTO(DataclassDTO[TeamCreate]):
    """Team Create."""

    config = dto.config()


@dataclass
class TeamUpdate:
    name: str | None = None
    description: str | None = None
    tags: list[str] | None = None


class TeamUpdateDTO(DataclassDTO[TeamUpdate]):
    """Team Update."""

    config = dto.config()
