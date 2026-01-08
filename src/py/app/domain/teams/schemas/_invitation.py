"""Team invitation schemas."""

from datetime import datetime
from uuid import UUID

from app.db.models._team_roles import TeamRoles
from app.lib.schema import CamelizedBaseStruct


class TeamInvitationCreate(CamelizedBaseStruct):
    email: str
    role: TeamRoles


class TeamInvitation(CamelizedBaseStruct):
    id: UUID
    email: str
    role: TeamRoles
    created_at: datetime
    updated_at: datetime
    is_accepted: bool = False
