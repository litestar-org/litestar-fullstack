"""Test data factories using Polyfactory aligned with UUIDv7AuditBase models."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any
from unittest.mock import AsyncMock, Mock, create_autospec
from uuid import UUID, uuid4

from polyfactory import Ignore, Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.db import models as m
from app.lib.email import AppEmailService


class UserFactory(SQLAlchemyFactory[m.User]):
    """Factory for User model."""

    __model__ = m.User
    __set_relationships__ = True

    id = Use(uuid4)
    email = Use(lambda: f"user{uuid4().hex[:8]}@example.com")
    name = Use(lambda: f"Test User {uuid4().hex[:8]}")
    username = Use(lambda: f"user{uuid4().hex[:8]}")
    hashed_password = "hashed_test_password_123"
    is_active = True
    is_verified = True
    is_superuser = False
    security_epoch = 1
    verified_at = Use(date.today)
    joined_at = Use(date.today)
    login_count = 0
    password_reset_at: datetime | None = None
    failed_reset_attempts = 0
    reset_locked_until: datetime | None = None

    roles = Ignore()
    teams = Ignore()
    oauth_accounts = Ignore()
    sessions = Ignore()
    mfa_factors = Ignore()
    passkeys = Ignore()
    api_keys = Ignore()


class AdminUserFactory(UserFactory):
    """Factory for superuser accounts."""

    email = Use(lambda: f"admin{uuid4().hex[:8]}@example.com")
    name = Use(lambda: f"Admin User {uuid4().hex[:8]}")
    is_superuser = True
    hashed_password = "hashed_admin_password_123"


class UnverifiedUserFactory(UserFactory):
    """Factory for unverified users."""

    is_verified = False
    verified_at: Any = None


class VerifiedUserFactory(UserFactory):
    """Factory for verified users."""

    is_verified = True
    verified_at = Use(date.today)


class TeamFactory(SQLAlchemyFactory[m.Team]):
    """Factory for Team model."""

    __model__ = m.Team
    __set_relationships__ = True

    id = Use(uuid4)
    name = Use(lambda: f"Test Team {uuid4().hex[:8]}")
    slug = Use(lambda: f"test-team-{uuid4().hex[:8]}")
    description = Use(lambda: f"Test team description {uuid4().hex[:8]}")
    is_active = True

    members = Ignore()
    invitations = Ignore()
    pending_invitations = Ignore()
    tags = Ignore()


class TeamMemberFactory(SQLAlchemyFactory[m.TeamMember]):
    """Factory for TeamMember model."""

    __model__ = m.TeamMember
    __set_relationships__ = True
    __check_model__ = False

    id = Use(uuid4)
    role = m.TeamRoles.MEMBER
    is_owner = False
    team_id: UUID | None = None
    user_id: UUID | None = None

    team = Ignore()
    user = Ignore()
    name = Ignore()
    email = Ignore()
    team_name = Ignore()


class UserOauthAccountFactory(SQLAlchemyFactory[m.UserOAuthAccount]):
    """Factory for UserOAuthAccount model."""

    __model__ = m.UserOAuthAccount
    __set_relationships__ = True
    __check_model__ = False

    id = Use(uuid4)
    oauth_name = "google"
    account_id = Use(lambda: f"oauth_{uuid4().hex}")
    account_email = Use(lambda: f"oauth{uuid4().hex[:8]}@gmail.com")
    access_token = Use(lambda: f"access_token_{uuid4().hex}")
    refresh_token = Use(lambda: f"refresh_token_{uuid4().hex}")
    expires_at: datetime | None = None
    token_expires_at = Use(lambda: datetime.now(UTC).replace(hour=23, minute=59, second=59))
    scope = "openid email profile"
    provider_user_data = Use(
        lambda: {
            "email": f"oauth{uuid4().hex[:8]}@gmail.com",
            "name": f"OAuth User {uuid4().hex[:8]}",
            "picture": f"https://example.com/avatar_{uuid4().hex[:8]}.jpg",
        }
    )
    last_login_at = Use(lambda: datetime.now(UTC))
    user_id: UUID | None = None

    user = Ignore()
    user_name = Ignore()
    user_email = Ignore()


class TeamInvitationFactory(SQLAlchemyFactory[m.TeamInvitation]):
    """Factory for TeamInvitation model."""

    __model__ = m.TeamInvitation
    __set_relationships__ = True

    id = Use(uuid4)
    email = Use(lambda: f"invite{uuid4().hex[:8]}@example.com")
    role = m.TeamRoles.MEMBER
    is_accepted = False
    invited_by_id: UUID | None = None
    invited_by_email = Use(lambda: f"inviter{uuid4().hex[:8]}@example.com")
    team_id: UUID | None = None

    team = Ignore()
    invited_by = Ignore()


class RoleFactory(SQLAlchemyFactory[m.Role]):
    """Factory for Role model."""

    __model__ = m.Role
    __set_relationships__ = True

    id = Use(uuid4)
    name = Use(lambda: f"test_role_{uuid4().hex[:8]}")
    slug = Use(lambda: f"test-role-{uuid4().hex[:8]}")
    description = Use(lambda: f"Test role description {uuid4().hex[:8]}")

    users = Ignore()


class UserRoleFactory(SQLAlchemyFactory[m.UserRole]):
    """Factory for UserRole model."""

    __model__ = m.UserRole
    __set_relationships__ = True
    __check_model__ = False

    id = Use(uuid4)
    assigned_at = Use(lambda: datetime.now(UTC))
    user_id: UUID | None = None
    role_id: UUID | None = None

    user = Ignore()
    role = Ignore()
    user_name = Ignore()
    user_email = Ignore()
    role_name = Ignore()
    role_slug = Ignore()


class TagFactory(SQLAlchemyFactory[m.Tag]):
    """Factory for Tag model."""

    __model__ = m.Tag
    __set_relationships__ = True

    id = Use(uuid4)
    name = Use(lambda: f"test_tag_{uuid4().hex[:8]}")
    slug = Use(lambda: f"test-tag-{uuid4().hex[:8]}")
    description = Use(lambda: f"Test tag description {uuid4().hex[:8]}")

    teams = Ignore()


async def create_user_with_team(session: Any, **kwargs: Any) -> tuple[m.User, m.Team]:
    """Create a user with an owned team inside the provided async session."""
    user = UserFactory.build(**kwargs)
    session.add(user)
    await session.flush()

    team = TeamFactory.build()
    session.add(team)
    await session.flush()

    membership = TeamMemberFactory.build(team_id=team.id, user_id=user.id, role=m.TeamRoles.ADMIN, is_owner=True)
    session.add(membership)
    return user, team


class EmailServiceFactory:
    """Factory for creating mock AppEmailService instances for unit tests."""

    @staticmethod
    def create_mock_service(
        *,
        send_result: bool = True,
    ) -> Mock:
        """Create a mock AppEmailService with configurable async delivery outcomes."""
        mock_service: Mock = create_autospec(AppEmailService, instance=True)
        mock_service.send_verification_email = AsyncMock(return_value=send_result)
        mock_service.send_welcome_email = AsyncMock(return_value=send_result)
        mock_service.send_password_reset_email = AsyncMock(return_value=send_result)
        mock_service.send_password_reset_confirmation_email = AsyncMock(return_value=send_result)
        mock_service.send_team_invitation_email = AsyncMock(return_value=send_result)
        return mock_service
