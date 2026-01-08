"""Test data factories using Polyfactory."""

from __future__ import annotations

import hashlib
from datetime import UTC, date, datetime, timedelta
from typing import Any, Protocol, cast, overload
from unittest.mock import AsyncMock, Mock, create_autospec
from uuid import uuid4

from polyfactory import Ignore, Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.db import models as m
from app.lib.email import EmailService


class _RawTokenCarrier(Protocol):
    raw_token: str


@overload
def get_raw_token(token: m.EmailVerificationToken) -> str: ...
@overload
def get_raw_token(token: m.PasswordResetToken) -> str: ...
@overload
def get_raw_token(token: m.RefreshToken) -> str: ...


def get_raw_token(token: object) -> str:
    return cast("_RawTokenCarrier", token).raw_token


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
    verified_at = Use(date.today)
    joined_at = Use(date.today)
    login_count = 0
    password_reset_at = None
    failed_reset_attempts = 0
    reset_locked_until = None
    # MFA fields - explicit None to avoid polyfactory generating naive datetimes
    totp_secret = None
    is_two_factor_enabled = False
    two_factor_confirmed_at = None
    backup_codes = None

    # Ignore relationships to avoid circular dependencies
    roles = Ignore()
    teams = Ignore()
    oauth_accounts = Ignore()
    verification_tokens = Ignore()
    reset_tokens = Ignore()
    refresh_tokens = Ignore()


class AdminUserFactory(UserFactory):
    """Factory for admin users."""

    email = Use(lambda: f"admin{uuid4().hex[:8]}@example.com")
    name = Use(lambda: f"Admin User {uuid4().hex[:8]}")
    is_superuser = True
    hashed_password = "hashed_admin_password_123"


class TeamFactory(SQLAlchemyFactory[m.Team]):
    """Factory for Team model."""

    __model__ = m.Team
    __set_relationships__ = True

    id = Use(uuid4)
    name = Use(lambda: f"Test Team {uuid4().hex[:8]}")
    slug = Use(lambda: f"test-team-{uuid4().hex[:8]}")
    description = Use(lambda: f"Test team description {uuid4().hex[:8]}")
    is_active = True

    # Ignore relationships
    members = Ignore()
    invitations = Ignore()
    pending_invitations = Ignore()
    tags = Ignore()


class TeamMemberFactory(SQLAlchemyFactory[m.TeamMember]):
    """Factory for TeamMember model."""

    __model__ = m.TeamMember
    __set_relationships__ = True
    __check_model__ = False  # Association proxies cause validation issues

    id = Use(uuid4)
    role = m.TeamRoles.MEMBER
    is_owner = False

    # These will be set by the caller
    team_id = None
    user_id = None

    # Ignore relationships and association proxies
    team = Ignore()
    user = Ignore()
    name = Ignore()
    email = Ignore()
    team_name = Ignore()


class EmailVerificationTokenFactory(SQLAlchemyFactory[m.EmailVerificationToken]):
    """Factory for EmailVerificationToken model."""

    __model__ = m.EmailVerificationToken
    __set_relationships__ = True

    id = Use(uuid4)
    token_hash = Ignore()
    email = Use(lambda: f"user{uuid4().hex[:8]}@example.com")
    expires_at = Use(lambda: datetime.now(UTC).replace(hour=23, minute=59, second=59))
    used_at = None

    # These will be set by the caller
    user_id = None

    # Ignore relationships
    user = Ignore()

    @classmethod
    def build(cls, **kwargs: Any) -> m.EmailVerificationToken:
        raw_token = kwargs.pop("raw_token", None)
        if raw_token is None:
            raw_token = uuid4().hex
        kwargs.setdefault("token_hash", hashlib.sha256(raw_token.encode()).hexdigest())
        token = super().build(**kwargs)
        setattr(token, "raw_token", raw_token)
        return token


class PasswordResetTokenFactory(SQLAlchemyFactory[m.PasswordResetToken]):
    """Factory for PasswordResetToken model."""

    __model__ = m.PasswordResetToken
    __set_relationships__ = True

    id = Use(uuid4)
    token_hash = Ignore()
    expires_at = Use(lambda: datetime.now(UTC).replace(hour=23, minute=59, second=59))
    used_at = None
    ip_address = "127.0.0.1"
    user_agent = "Test User Agent"

    # These will be set by the caller
    user_id = None

    # Ignore relationships
    user = Ignore()

    @classmethod
    def build(cls, **kwargs: Any) -> m.PasswordResetToken:
        raw_token = kwargs.pop("raw_token", None)
        if raw_token is None:
            raw_token = uuid4().hex
        kwargs.setdefault("token_hash", hashlib.sha256(raw_token.encode()).hexdigest())
        token = super().build(**kwargs)
        setattr(token, "raw_token", raw_token)
        return token


class RefreshTokenFactory(SQLAlchemyFactory[m.RefreshToken]):
    """Factory for RefreshToken model."""

    __model__ = m.RefreshToken
    __set_relationships__ = True

    id = Use(uuid4)
    token_hash = Ignore()
    family_id = Use(uuid4)
    expires_at = Use(lambda: datetime.now(UTC) + timedelta(days=7))
    revoked_at = None
    device_info = "Mozilla/5.0 (Test Device) TestBrowser/1.0"

    # These will be set by the caller
    user_id = None

    # Ignore relationships
    user = Ignore()

    @classmethod
    def build(cls, **kwargs: Any) -> m.RefreshToken:
        raw_token = kwargs.pop("raw_token", None)
        if raw_token is None:
            raw_token = uuid4().hex + uuid4().hex  # Make it longer for security
        kwargs.setdefault("token_hash", hashlib.sha256(raw_token.encode()).hexdigest())
        token = super().build(**kwargs)
        setattr(token, "raw_token", raw_token)
        return token


class UserOauthAccountFactory(SQLAlchemyFactory[m.UserOAuthAccount]):
    """Factory for UserOauthAccount model."""

    __model__ = m.UserOAuthAccount
    __set_relationships__ = True
    __check_model__ = False  # Association proxies cause validation issues

    id = Use(uuid4)
    oauth_name = "google"
    account_id = Use(lambda: f"oauth_{uuid4().hex}")
    account_email = Use(lambda: f"oauth{uuid4().hex[:8]}@gmail.com")
    access_token = Use(lambda: f"access_token_{uuid4().hex}")
    refresh_token = Use(lambda: f"refresh_token_{uuid4().hex}")
    expires_at = None
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

    # These will be set by the caller
    user_id = None

    # Ignore relationships and association proxies
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
    invited_by_id = None
    invited_by_email = Use(lambda: f"inviter{uuid4().hex[:8]}@example.com")

    # These will be set by the caller
    team_id = None

    # Ignore relationships
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

    # Ignore relationships
    users = Ignore()


class UserRoleFactory(SQLAlchemyFactory[m.UserRole]):
    """Factory for UserRole model."""

    __model__ = m.UserRole
    __set_relationships__ = True
    __check_model__ = False  # Association proxies cause validation issues

    id = Use(uuid4)
    assigned_at = Use(lambda: datetime.now(UTC))

    # These will be set by the caller
    user_id = None
    role_id = None

    # Ignore relationships and association proxies
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

    # Ignore relationships
    teams = Ignore()


# Convenience functions for creating complex test scenarios


async def create_user_with_team(session: Any, **kwargs: Any) -> tuple[m.User, m.Team]:
    """Create a user with an associated team."""
    user = UserFactory.build(**kwargs)
    session.add(user)
    await session.flush()  # Get the user ID

    team = TeamFactory.build()
    session.add(team)
    await session.flush()  # Get the team ID

    # Create team membership
    membership = TeamMemberFactory.build(team_id=team.id, user_id=user.id, role=m.TeamRoles.ADMIN, is_owner=True)
    session.add(membership)

    return user, team


async def create_team_with_members(session: Any, member_count: int = 3, **kwargs: Any) -> tuple[m.Team, list[m.User]]:
    """Create a team with multiple members."""
    # Create team owner
    owner = UserFactory.build()
    session.add(owner)
    await session.flush()

    team = TeamFactory.build(**kwargs)
    session.add(team)
    await session.flush()

    # Create owner membership
    owner_membership = TeamMemberFactory.build(team_id=team.id, user_id=owner.id, role=m.TeamRoles.ADMIN, is_owner=True)
    session.add(owner_membership)

    # Create additional members
    members = [owner]
    for _ in range(member_count - 1):
        member = UserFactory.build()
        session.add(member)
        await session.flush()

        membership = TeamMemberFactory.build(team_id=team.id, user_id=member.id, role=m.TeamRoles.MEMBER)
        session.add(membership)
        members.append(member)

    return team, members


def create_user_with_oauth_account(
    session: Any, provider: str = "google", **kwargs: Any
) -> tuple[m.User, m.UserOAuthAccount]:
    """Create a user with an OAuth account."""
    user = UserFactory.build(**kwargs)
    session.add(user)
    session.flush()

    oauth_account = UserOauthAccountFactory.build(user_id=user.id, provider=provider)
    session.add(oauth_account)

    return user, oauth_account


# Email Service Factory
class EmailServiceFactory:
    """Factory for creating mock EmailService instances for testing."""

    @staticmethod
    def create_mock_service(
        enabled: bool = True,
        send_email_result: bool = True,
        send_template_result: bool = True,
        base_url: str = "http://test.example.com",
        app_name: str = "Test App",
    ) -> Mock:
        """Create a mock EmailService with configurable behavior.

        Args:
            enabled: Whether email service should be enabled
            send_email_result: Return value for send_email method
            send_template_result: Return value for send_template_email method
            base_url: Base URL for the application
            app_name: Application name

        Returns:
            Mock EmailService instance
        """
        mock_service = create_autospec(EmailService, instance=True)

        # Configure settings mock
        mock_settings = Mock()
        mock_settings.ENABLED = enabled
        mock_settings.FROM_EMAIL = "test@example.com"
        mock_settings.FROM_NAME = "Test Service"
        mock_settings.SMTP_HOST = "localhost"
        mock_settings.SMTP_PORT = 587
        mock_settings.USE_TLS = True
        mock_settings.USE_SSL = False
        mock_settings.TIMEOUT = 30
        mock_settings.SMTP_USER = "testuser"
        mock_settings.SMTP_PASSWORD = "testpass"

        mock_app_settings = Mock()
        mock_app_settings.URL = base_url
        mock_app_settings.NAME = app_name

        mock_service.settings = mock_settings
        mock_service.app_settings = mock_app_settings
        mock_service.base_url = base_url
        mock_service.app_name = app_name

        # Configure async methods
        mock_service.send_email = AsyncMock(return_value=send_email_result)
        mock_service.send_template_email = AsyncMock(return_value=send_template_result)
        mock_service.send_verification_email = AsyncMock(return_value=send_email_result)
        mock_service.send_welcome_email = AsyncMock(return_value=send_email_result)
        mock_service.send_password_reset_email = AsyncMock(return_value=send_email_result)
        mock_service.send_password_reset_confirmation_email = AsyncMock(return_value=send_email_result)
        mock_service.send_team_invitation_email = AsyncMock(return_value=send_email_result)

        return mock_service

    @staticmethod
    def create_failing_service() -> Mock:
        """Create a mock EmailService that fails all operations."""
        return EmailServiceFactory.create_mock_service(
            enabled=True,
            send_email_result=False,
            send_template_result=False,
        )

    @staticmethod
    def create_disabled_service() -> Mock:
        """Create a mock EmailService that is disabled."""
        return EmailServiceFactory.create_mock_service(enabled=False)


# Enhanced User Factories for Email Verification States
class UnverifiedUserFactory(UserFactory):
    """Factory for unverified users."""

    is_verified = False
    verified_at = None


class VerifiedUserFactory(UserFactory):
    """Factory for verified users."""

    is_verified = True
    verified_at = Use(date.today)


class PendingVerificationUserFactory(UserFactory):
    """Factory for users with pending email verification."""

    is_verified = False
    verified_at = None
    is_active = False


class ExpiredTokenUserFactory(UserFactory):
    """Factory for users with expired verification tokens."""

    is_verified = False
    verified_at = None


# Enhanced Token Factories
class ValidEmailVerificationTokenFactory(EmailVerificationTokenFactory):
    """Factory for valid (unexpired, unused) email verification tokens."""

    expires_at = Use(lambda: datetime.now(UTC) + timedelta(hours=24))
    used_at = None


class ExpiredEmailVerificationTokenFactory(EmailVerificationTokenFactory):
    """Factory for expired email verification tokens."""

    expires_at = Use(lambda: datetime.now(UTC) - timedelta(hours=1))
    used_at = None


class UsedEmailVerificationTokenFactory(EmailVerificationTokenFactory):
    """Factory for used email verification tokens."""

    expires_at = Use(lambda: datetime.now(UTC) + timedelta(hours=24))
    used_at = Use(lambda: datetime.now(UTC))


class ValidPasswordResetTokenFactory(PasswordResetTokenFactory):
    """Factory for valid password reset tokens."""

    expires_at = Use(lambda: datetime.now(UTC) + timedelta(hours=1))
    used_at = None


class ExpiredPasswordResetTokenFactory(PasswordResetTokenFactory):
    """Factory for expired password reset tokens."""

    expires_at = Use(lambda: datetime.now(UTC) - timedelta(minutes=30))
    used_at = None


class UsedPasswordResetTokenFactory(PasswordResetTokenFactory):
    """Factory for used password reset tokens."""

    expires_at = Use(lambda: datetime.now(UTC) + timedelta(hours=1))
    used_at = Use(lambda: datetime.now(UTC))


# Enhanced convenience functions for email verification scenarios


def create_user_with_verification_token(
    session: Any, token_state: str = "valid", **user_kwargs: Any
) -> tuple[m.User, m.EmailVerificationToken]:
    """Create a user with an email verification token in specified state.

    Args:
        session: Database session
        token_state: State of token ("valid", "expired", "used")
        **user_kwargs: Additional user factory kwargs

    Returns:
        Tuple of (User, EmailVerificationToken)
    """
    # Create user based on token state
    if token_state == "valid":
        user = PendingVerificationUserFactory.build(**user_kwargs)
        token_factory = ValidEmailVerificationTokenFactory
    elif token_state == "expired":
        user = UnverifiedUserFactory.build(**user_kwargs)
        token_factory = ExpiredEmailVerificationTokenFactory
    elif token_state == "used":
        user = VerifiedUserFactory.build(**user_kwargs)
        token_factory = UsedEmailVerificationTokenFactory
    else:
        msg = f"Invalid token_state: {token_state}. Must be 'valid', 'expired', or 'used'"
        raise ValueError(msg)

    session.add(user)
    session.flush()

    token = token_factory.build(user_id=user.id, email=user.email)
    session.add(token)

    return user, token


def create_user_with_password_reset_token(
    session: Any, token_state: str = "valid", ip_address: str = "127.0.0.1", **user_kwargs: Any
) -> tuple[m.User, m.PasswordResetToken]:
    """Create a user with a password reset token in specified state.

    Args:
        session: Database session
        token_state: State of token ("valid", "expired", "used")
        ip_address: IP address for the reset request
        **user_kwargs: Additional user factory kwargs

    Returns:
        Tuple of (User, PasswordResetToken)
    """
    user = VerifiedUserFactory.build(**user_kwargs)
    session.add(user)
    session.flush()

    if token_state == "valid":
        token_factory = ValidPasswordResetTokenFactory
    elif token_state == "expired":
        token_factory = ExpiredPasswordResetTokenFactory
    elif token_state == "used":
        token_factory = UsedPasswordResetTokenFactory
    else:
        msg = f"Invalid token_state: {token_state}. Must be 'valid', 'expired', or 'used'"
        raise ValueError(msg)

    token = token_factory.build(user_id=user.id, ip_address=ip_address)
    session.add(token)

    return user, token


def create_email_verification_scenario(
    session: Any, scenario: str = "pending_verification", **kwargs: Any
) -> dict[str, Any]:
    """Create a complete email verification test scenario.

    Args:
        session: Database session
        scenario: Type of scenario to create
        **kwargs: Additional factory kwargs

    Returns:
        Dictionary with scenario objects
    """
    scenarios = {
        "pending_verification": {
            "description": "User needs to verify email",
            "user_factory": PendingVerificationUserFactory,
            "token_factory": ValidEmailVerificationTokenFactory,
            "expected_verified": False,
        },
        "successful_verification": {
            "description": "User successfully verified email",
            "user_factory": VerifiedUserFactory,
            "token_factory": UsedEmailVerificationTokenFactory,
            "expected_verified": True,
        },
        "expired_token": {
            "description": "User has expired verification token",
            "user_factory": UnverifiedUserFactory,
            "token_factory": ExpiredEmailVerificationTokenFactory,
            "expected_verified": False,
        },
        "no_token": {
            "description": "User exists but has no verification token",
            "user_factory": UnverifiedUserFactory,
            "token_factory": None,
            "expected_verified": False,
        },
    }

    if scenario not in scenarios:
        available = ", ".join(scenarios.keys())
        msg = f"Invalid scenario: {scenario}. Available: {available}"
        raise ValueError(msg)

    config = scenarios[scenario]
    user = config["user_factory"].build(**kwargs)
    session.add(user)
    session.flush()

    result = {
        "user": user,
        "token": None,
        "scenario": scenario,
        "description": config["description"],
        "expected_verified": config["expected_verified"],
    }

    if config["token_factory"]:
        token = config["token_factory"].build(user_id=user.id, email=user.email)
        session.add(token)
        result["token"] = token

    return result


def create_bulk_users_with_verification_states(
    session: Any,
    count: int = 10,
    verified_ratio: float = 0.7,
    pending_ratio: float = 0.2,
) -> dict[str, list[m.User]]:
    """Create multiple users with different verification states.

    Args:
        session: Database session
        count: Total number of users to create
        verified_ratio: Ratio of verified users (0.0-1.0)
        pending_ratio: Ratio of pending verification users (0.0-1.0)

    Returns:
        Dictionary with lists of users by state
    """
    if verified_ratio + pending_ratio > 1.0:
        msg = "verified_ratio + pending_ratio cannot exceed 1.0"
        raise ValueError(msg)

    verified_count = int(count * verified_ratio)
    pending_count = int(count * pending_ratio)
    unverified_count = count - verified_count - pending_count

    result = {
        "verified": [],
        "pending": [],
        "unverified": [],
    }

    # Create verified users
    for _ in range(verified_count):
        user = VerifiedUserFactory.build()
        session.add(user)
        result["verified"].append(user)

    # Create pending verification users
    for _ in range(pending_count):
        user = PendingVerificationUserFactory.build()
        session.add(user)
        session.flush()

        # Add valid verification token
        token = ValidEmailVerificationTokenFactory.build(user_id=user.id, email=user.email)
        session.add(token)
        result["pending"].append(user)

    # Create unverified users
    for _ in range(unverified_count):
        user = UnverifiedUserFactory.build()
        session.add(user)
        result["unverified"].append(user)

    return result
