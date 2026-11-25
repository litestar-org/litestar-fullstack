"""Team membership database service enforcing duplicate-membership and ownership rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.exceptions import IntegrityError
from advanced_alchemy.extensions.litestar import service
from litestar.exceptions import HTTPException
from sqlalchemy import true

from app.db import models as m

if TYPE_CHECKING:
    from uuid import UUID

ALREADY_A_MEMBER = "User is already a member of this team"


class TeamMemberService(service.SQLAlchemyAsyncRepositoryService[m.TeamMember]):
    """Handles team memberships and the rules that keep every team owned."""

    async def add_member(self, team_id: UUID, user_id: UUID) -> m.TeamMember:
        """Add a user to a team as a regular member.

        Returns:
            The new membership.

        Raises:
            IntegrityError: If the user is already a member of the team.
        """
        if await self.exists(team_id=team_id, user_id=user_id):
            raise IntegrityError(ALREADY_A_MEMBER)
        return await self.create(
            {"team_id": team_id, "user_id": user_id, "role": m.TeamRoles.MEMBER, "is_owner": False},
            auto_commit=True,
        )

    async def remove_member(self, team_id: UUID, user_id: UUID) -> None:
        """Remove a user from a team, failing with ``IntegrityError`` when they are not a member.

        Raises:
            HTTPException: If the user is the sole owner of the team.
        """
        membership = await self._get_membership(team_id, user_id)
        if membership.is_owner:
            owner_count = await self.count(m.TeamMember.team_id == team_id, m.TeamMember.is_owner.is_(true()))
            if owner_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot remove the sole team owner without transferring ownership",
                )
        await self.delete(membership.id, auto_commit=True)

    async def change_role(self, team_id: UUID, user_id: UUID, role: m.TeamRoles) -> m.TeamMember:
        """Change a member's role, failing with ``IntegrityError`` when the user is not a member.

        Returns:
            The updated membership.

        Raises:
            HTTPException: If the change would demote a team owner from the ``ADMIN`` role.
        """
        membership = await self._get_membership(team_id, user_id)
        if membership.is_owner and role != m.TeamRoles.ADMIN:
            raise HTTPException(status_code=400, detail="Cannot demote a team owner from ADMIN role")
        return await self.update(item_id=membership.id, data={"role": role}, auto_commit=True)

    async def _get_membership(self, team_id: UUID, user_id: UUID) -> m.TeamMember:
        membership = await self.get_one_or_none(team_id=team_id, user_id=user_id)
        if membership is None:
            msg = "User is not a member of this team."
            raise IntegrityError(msg)
        return membership
