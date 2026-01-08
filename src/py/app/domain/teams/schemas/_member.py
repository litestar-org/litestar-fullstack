"""Team member schemas."""

from uuid import UUID

from app.db.models._team_roles import TeamRoles
from app.lib.schema import CamelizedBaseStruct


class TeamMember(CamelizedBaseStruct):
    id: UUID
    user_id: UUID
    email: str
    name: str | None = None
    role: TeamRoles | None = None
    is_owner: bool | None = False

    def __post_init__(self) -> None:
        """Set default role if not provided."""
        if self.role is None:
            self.role = TeamRoles.MEMBER


class TeamMemberModify(CamelizedBaseStruct):
    """Team Member Modify."""

    user_name: str


class TeamMemberUpdate(CamelizedBaseStruct):
    """Team Member Update."""

    role: TeamRoles
