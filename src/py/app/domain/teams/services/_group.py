"""Shared-session ServiceGroup bundling team, member, invitation, and tag services."""

from uuid import UUID

from advanced_alchemy.service import ServiceGroup
from litestar.exceptions import HTTPException, PermissionDeniedException

from app.db import models as m
from app.domain.tags.services import TagService
from app.domain.teams.services._team import TeamService
from app.domain.teams.services._team_invitation import TeamInvitationService
from app.domain.teams.services._team_member import ALREADY_A_MEMBER, TeamMemberService


class TeamServices(ServiceGroup):
    """Unified team-domain service group sharing a single SQLAlchemy async session."""

    teams: TeamService
    members: TeamMemberService
    invitations: TeamInvitationService
    tags: TagService

    async def accept_invitation(self, invitation_id: UUID, *, team_id: UUID, user: m.User) -> None:
        """Add ``user`` to the team and mark their invitation accepted in one transaction.

        Raises:
            HTTPException: If the invitation was already accepted or ``user`` is already a member of the team.
            PermissionDeniedException: If the invitation is addressed to someone other than ``user``.
        """
        invitation = await self.invitations.get_for_team(invitation_id, team_id)
        if invitation.is_accepted:
            raise HTTPException(status_code=400, detail="Invitation has already been accepted")
        if not self.invitations.is_addressed_to(invitation, user):
            raise PermissionDeniedException(detail="You are not authorized to accept this invitation")
        if await self.members.exists(team_id=team_id, user_id=user.id):
            raise HTTPException(status_code=400, detail=ALREADY_A_MEMBER)
        await self.members.create(
            {"team_id": team_id, "user_id": user.id, "role": invitation.role, "is_owner": False},
        )
        await self.invitations.update(item_id=invitation_id, data={"is_accepted": True}, auto_commit=True)
