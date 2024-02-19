import msgspec
from advanced_alchemy.extensions.litestar.dto import SQLAlchemyDTO

from app.db.models import Team
from app.lib import dto

__all__ = ["TeamCreate", "TeamDTO", "TeamUpdate"]


# database model


class TeamDTO(SQLAlchemyDTO[Team]):
    config = dto.config(
        backend="sqlalchemy",
        exclude={
            "created_at",
            "updated_at",
            "members.team",
            "members.user",
            "members.created_at",
            "members.updated_at",
            "members.id",
            "members.user_name",
            "members.user_email",
            "members.team_name",
            "invitations",
            "tags.created_at",
            "tags.updated_at",
            "pending_invitations",
        },
        max_nested_depth=1,
    )


class TeamCreate(msgspec.Struct):
    name: str
    description: str | None = None
    tags: list[str] | None = None


class TeamUpdate(msgspec.Struct):
    name: str | None = None
    description: str | None = None
    tags: list[str] | None = None
