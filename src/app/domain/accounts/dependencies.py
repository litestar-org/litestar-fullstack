"""User Account Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import joinedload, load_only, noload, selectinload

from app.db.models import Role, Team, TeamMember, User, UserRole
from app.domain.accounts.services import RoleService, UserRoleService, UserService

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_users_service(db_session: AsyncSession) -> AsyncGenerator[UserService, None]:
    """Construct repository and service objects for the request."""
    async with UserService.new(
        session=db_session,
        statement=select(User)
        .order_by(User.email)
        .options(
            load_only(
                User.id,
                User.email,
                User.name,
                User.hashed_password,
                User.is_superuser,
                User.is_active,
                User.is_verified,
            ),
            selectinload(User.roles).options(joinedload(UserRole.role, innerjoin=True).options(noload("*"))),
            selectinload(User.teams).options(
                joinedload(TeamMember.team, innerjoin=True).options(load_only(Team.name)),
                load_only(
                    TeamMember.id,
                    TeamMember.user_id,
                    TeamMember.team_id,
                    TeamMember.role,
                    TeamMember.is_owner,
                ),
            ),
        ),
    ) as service:
        yield service


async def provide_roles_service(db_session: AsyncSession | None = None) -> AsyncGenerator[RoleService, None]:
    """Provide roles service.

    Args:
        db_session (AsyncSession | None, optional): current database session. Defaults to None.

    Returns:
        RoleService: A role service object
    """
    async with RoleService.new(
        session=db_session,
        statement=select(Role).options(selectinload(Role.users).options(joinedload(UserRole.user, innerjoin=True))),
    ) as service:
        yield service


async def provide_user_roles_service(db_session: AsyncSession | None = None) -> AsyncGenerator[UserRoleService, None]:
    """Provide user roles service.

    Args:
        db_session (AsyncSession | None, optional): current database session. Defaults to None.

    Returns:
        UserRoleService: A user role service object
    """
    async with UserRoleService.new(
        session=db_session,
        statement=select(UserRole).options(noload("*")),
    ) as service:
        yield service
