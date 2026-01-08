"""Account domain integration test fixtures.

These fixtures provide service instances for account-related tests.
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

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def user_service(session: AsyncSession) -> AsyncGenerator[UserService, None]:
    """Create UserService instance with test session."""
    async with UserService.new(session, load=[m.User.roles, m.User.oauth_accounts, m.User.teams]) as service:
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
async def user_role_service(session: AsyncSession) -> AsyncGenerator[UserRoleService, None]:
    """Create UserRoleService instance."""
    async with UserRoleService.new(session) as service:
        yield service


@pytest.fixture
async def user_oauth_service(session: AsyncSession) -> AsyncGenerator[UserOAuthAccountService, None]:
    """Create UserOAuthAccountService instance."""
    async with UserOAuthAccountService.new(session) as service:
        yield service
