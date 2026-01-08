"""Team domain integration test fixtures.

These fixtures provide service instances for team-related tests.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from app.db import models as m
from app.domain.tags.services import TagService
from app.domain.teams.services import TeamInvitationService, TeamMemberService, TeamService

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def team_service(session: AsyncSession) -> AsyncGenerator[TeamService, None]:
    """Create TeamService instance with test session."""
    async with TeamService.new(session, load=[m.Team.tags, m.Team.members]) as service:
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
async def tag_service(session: AsyncSession) -> AsyncGenerator[TagService, None]:
    """Create TagService instance."""
    async with TagService.new(session) as service:
        yield service
