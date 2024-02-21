import msgspec
from uuid_utils import UUID

from app.db.models.team_roles import TeamRoles


class TeamTag(msgspec.Struct):
    id: UUID
    slug: str
    name: str


class TeamMember(msgspec.Struct):
    id: UUID
    user_id: UUID
    email: str
    name: str | None = None
    role: TeamRoles | None = TeamRoles.MEMBER
    is_owner: bool | None = False


class Team(msgspec.Struct):
    name: str
    description: str | None = None
    members: list[TeamMember] = []
    tags: list[TeamTag] = []


class TeamCreate(msgspec.Struct):
    name: str
    description: str | None = None
    tags: list[str] = []


class TeamUpdate(msgspec.Struct):
    name: str | None = None
    description: str | None = None
    tags: list[str] | None | msgspec.UnsetType = msgspec.UNSET
