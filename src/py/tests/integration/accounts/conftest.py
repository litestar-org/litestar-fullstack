"""Account domain integration test fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from app.db import models as m
from app.domain.accounts.services import (
    RoleService,
    UserRoleService,
    UserService,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.anyio


@pytest.fixture
async def user_service(session: AsyncSession) -> AsyncGenerator[UserService, None]:
    """Create UserService instance with test session."""
    async with UserService.new(
        session,
        load=[m.User.roles, m.User.oauth_accounts, m.User.teams, m.User.mfa_factors],
    ) as service:
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
