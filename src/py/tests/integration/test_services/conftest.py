"""Service integration test fixtures.

These tests verify service behavior against a real database.
Each test gets a clean database state via the db_cleanup fixture.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from app.db import models as m
from app.domain.accounts.services import (
    EmailVerificationTokenService,
    PasswordResetService,
    RefreshTokenService,
    RoleService,
    UserOAuthAccountService,
    UserRoleService,
    UserService,
)
from app.domain.tags.services import TagService
from app.domain.teams.services import TeamInvitationService, TeamMemberService, TeamService

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession

# -----------------------------------------------------------------------------
# Service fixtures - use Service.new(session) for direct session access
#
# Note: These services are created with minimal loading options.
# For full production loading patterns (eager loading, etc.), use the
# service providers from app.domain.*.deps with provide_services().
# -----------------------------------------------------------------------------


@pytest.fixture
async def user_service(session: AsyncSession) -> AsyncGenerator[UserService, None]:
    """Create UserService instance with test session."""
    async with UserService.new(session, load=[m.User.roles, m.User.oauth_accounts, m.User.teams]) as service:
        yield service


@pytest.fixture
async def team_service(session: AsyncSession) -> AsyncGenerator[TeamService, None]:
    """Create TeamService instance with test session."""
    async with TeamService.new(session, load=[m.Team.tags, m.Team.members]) as service:
        yield service


@pytest.fixture
async def email_verification_service(session: AsyncSession) -> AsyncGenerator[EmailVerificationTokenService, None]:
    """Create EmailVerificationTokenService instance."""
    async with EmailVerificationTokenService.new(session) as service:
        yield service


@pytest.fixture
async def password_reset_service(session: AsyncSession) -> AsyncGenerator[PasswordResetService, None]:
    """Create PasswordResetService instance."""
    async with PasswordResetService.new(session) as service:
        yield service


@pytest.fixture
async def refresh_token_service(session: AsyncSession) -> AsyncGenerator[RefreshTokenService, None]:
    """Create RefreshTokenService instance."""
    async with RefreshTokenService.new(session) as service:
        yield service


@pytest.fixture
async def role_service(session: AsyncSession) -> AsyncGenerator[RoleService, None]:
    """Create RoleService instance."""
    async with RoleService.new(session) as service:
        yield service


@pytest.fixture
async def tag_service(session: AsyncSession) -> AsyncGenerator[TagService, None]:
    """Create TagService instance."""
    async with TagService.new(session) as service:
        yield service


@pytest.fixture
async def team_member_service(session: AsyncSession) -> AsyncGenerator[TeamMemberService, None]:
    """Create TeamMemberService instance."""
    async with TeamMemberService.new(session) as service:
        yield service


@pytest.fixture
async def team_invitation_service(session: AsyncSession) -> AsyncGenerator[TeamInvitationService, None]:
    """Create TeamInvitationService instance."""
    async with TeamInvitationService.new(session) as service:
        yield service


@pytest.fixture
async def user_role_service(session: AsyncSession) -> AsyncGenerator[UserRoleService, None]:
    """Create UserRoleService instance."""
    async with UserRoleService.new(session) as service:
        yield service


@pytest.fixture
async def user_oauth_service(session: AsyncSession) -> AsyncGenerator[UserOAuthAccountService, None]:
    """Create UserOAuthAccountService instance."""
    async with UserOAuthAccountService.new(session) as service:
        yield service
