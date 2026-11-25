"""Team invitation database service enforcing who may be invited and who may decline."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.extensions.litestar import service
from litestar.exceptions import HTTPException, PermissionDeniedException
from litestar_security.accounts import normalize_identifier

from app.db import models as m
from app.domain.teams.services._team_member import ALREADY_A_MEMBER

if TYPE_CHECKING:
    from uuid import UUID


class TeamInvitationService(service.SQLAlchemyAsyncRepositoryService[m.TeamInvitation]):
    """Handles team invitations from issue through the invitee's response."""

    async def to_model_on_create(
        self, data: service.ModelDictT[m.TeamInvitation]
    ) -> service.ModelDictT[m.TeamInvitation]:
        """Resolve inviter metadata before creating an invitation.

        Returns:
            Normalized invitation payload with inviter fields populated.
        """
        return self._normalize_email(await self._populate_inviter(service.schema_dump(data)))

    async def to_model_on_update(
        self, data: service.ModelDictT[m.TeamInvitation]
    ) -> service.ModelDictT[m.TeamInvitation]:
        """Resolve inviter metadata before updating an invitation.

        Returns:
            Normalized invitation payload with inviter fields populated.
        """
        return self._normalize_email(await self._populate_inviter(service.schema_dump(data)))

    async def to_model_on_upsert(
        self, data: service.ModelDictT[m.TeamInvitation]
    ) -> service.ModelDictT[m.TeamInvitation]:
        """Resolve inviter metadata before upserting an invitation.

        Returns:
            Normalized invitation payload with inviter fields populated.
        """
        return self._normalize_email(await self._populate_inviter(service.schema_dump(data)))

    async def invite(
        self,
        team: m.Team,
        *,
        email: str,
        role: m.TeamRoles,
        invited_by: m.User,
    ) -> m.TeamInvitation:
        """Invite the person at ``email`` to join ``team`` with ``role``, matching members regardless of letter case.

        Returns:
            The pending invitation.

        Raises:
            HTTPException: If the invitee is already a member of the team.
        """
        invitee_email = normalize_identifier(email)
        if any(normalize_identifier(member.email) == invitee_email for member in team.members):
            raise HTTPException(status_code=400, detail=ALREADY_A_MEMBER)
        return await self.create(
            {"email": invitee_email, "role": role, "team_id": team.id, "invited_by": invited_by},
            auto_commit=True,
        )

    async def get_for_team(self, invitation_id: UUID, team_id: UUID) -> m.TeamInvitation:
        """Load an invitation that must have been issued by ``team_id``.

        Returns:
            The invitation.

        Raises:
            HTTPException: If the invitation belongs to a different team.
        """
        invitation = await self.get(invitation_id)
        if invitation.team_id != team_id:
            raise HTTPException(status_code=400, detail="Invitation does not belong to this team")
        return invitation

    async def reject(self, invitation_id: UUID, *, team_id: UUID, user: m.User) -> None:
        """Delete a team's invitation on behalf of the invitee who declines it.

        Raises:
            PermissionDeniedException: If the invitation is addressed to someone other than ``user``.
        """
        invitation = await self.get_for_team(invitation_id, team_id)
        if not self.is_addressed_to(invitation, user):
            raise PermissionDeniedException(detail="You are not authorized to reject this invitation")
        await self.delete(invitation.id, auto_commit=True)

    @staticmethod
    def is_addressed_to(invitation: m.TeamInvitation, user: m.User) -> bool:
        """Return whether ``invitation`` was sent to ``user``'s email address, ignoring letter case."""
        return normalize_identifier(invitation.email) == normalize_identifier(user.email)

    async def _populate_inviter(
        self, data: service.ModelDictT[m.TeamInvitation]
    ) -> service.ModelDictT[m.TeamInvitation]:
        if not service.is_dict(data):
            return data
        if (inviter := data.pop("invited_by", None)) is None:
            return data
        if service.is_dict_without_field(data, "invited_by_id"):
            data["invited_by_id"] = inviter.id
        if service.is_dict_without_field(data, "invited_by_email"):
            data["invited_by_email"] = inviter.email
        return data

    @staticmethod
    def _normalize_email(data: service.ModelDictT[m.TeamInvitation]) -> service.ModelDictT[m.TeamInvitation]:
        if service.is_dict_with_field(data, "email"):
            data["email"] = normalize_identifier(str(data["email"]))
        return data
