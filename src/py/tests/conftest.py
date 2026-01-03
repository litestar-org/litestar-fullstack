from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime, timedelta

from app.db import models as m
from app.domain.accounts.services import (
    EmailVerificationTokenService,
    PasswordResetService,
    RoleService,
    UserOAuthAccountService,
    UserRoleService,
    UserService,
)
from app.domain.tags.services import TagService
from app.domain.teams.services import TeamInvitationService, TeamMemberService, TeamService
from app.lib.crypt import get_password_hash
from app.lib.email import EmailService

# Set test environment before any other imports
os.environ.update(
    {
        "SECRET_KEY": "secret-key",
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "DATABASE_ECHO": "false",
        "DATABASE_ECHO_POOL": "false",
        "SAQ_USE_SERVER_LIFESPAN": "False",
        "SAQ_WEB_ENABLED": "True",
        "SAQ_PROCESSES": "1",
        "SAQ_CONCURRENCY": "1",
        "VITE_PORT": "3006",
        "VITE_DEV_MODE": "True",
        "EMAIL_ENABLED": "false",
    }
)

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from advanced_alchemy.base import UUIDAuditBase
from litestar.testing import AsyncTestClient
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from litestar import Litestar
    from pytest import MonkeyPatch
    from pytest_databases.docker.postgres import PostgresService
    from sqlalchemy.ext.asyncio import AsyncEngine


pytestmark = pytest.mark.anyio
pytest_plugins = [
    "tests.data_fixtures",
    "pytest_databases.docker",
    "pytest_databases.docker.postgres",
]


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def _patch_settings(monkeypatch: MonkeyPatch) -> None:
    """Patch the settings - environment already set at module level."""


@pytest.fixture(name="engine")
async def fx_engine(postgres_service: PostgresService) -> AsyncGenerator[AsyncEngine, None]:
    """PostgreSQL instance for testing.

    Returns:
        Async SQLAlchemy engine instance.
    """
    engine = create_async_engine(
        URL(
            drivername="postgresql+psycopg",
            username=postgres_service.user,
            password=postgres_service.password,
            host=postgres_service.host,
            port=postgres_service.port,
            database=postgres_service.database,
            query={},  # type:ignore[arg-type]
        ),
        echo=False,
        poolclass=NullPool,
    )

    # Create all tables
    metadata = UUIDAuditBase.registry.metadata
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

    yield engine

    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
    await engine.dispose()


@pytest.fixture(name="sessionmaker")
async def fx_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create sessionmaker factory."""
    return async_sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture
async def session(sessionmaker: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    async with sessionmaker() as session:
        yield session


@pytest.fixture
def app() -> Litestar:
    """Create Litestar app for testing."""

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

    from app.server.asgi import create_app

    return create_app()


@pytest.fixture
async def client(app: Litestar) -> AsyncGenerator[AsyncTestClient, None]:
    """Create test client."""
    async with AsyncTestClient(app=app) as client:
        yield client


@pytest.fixture
async def user_service(sessionmaker: async_sessionmaker[AsyncSession]) -> AsyncGenerator[UserService, None]:
    """Create UserService instance."""

    async with UserService.new(sessionmaker()) as service:
        yield service


@pytest.fixture
async def team_service(sessionmaker: async_sessionmaker[AsyncSession]) -> AsyncGenerator[TeamService, None]:
    """Create TeamService instance."""

    async with TeamService.new(sessionmaker()) as service:
        yield service


@pytest.fixture
async def test_user(session: AsyncSession) -> AsyncGenerator[m.User, None]:
    """Create a test user."""

    # Use unique email per test to avoid conflicts
    unique_id = str(uuid4())[:8]
    user = m.User(
        id=uuid4(),
        email=f"user{unique_id}@example.com",
        name="Test User",
        hashed_password=await get_password_hash("TestPassword123!"),
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    yield user


@pytest.fixture
async def admin_user(session: AsyncSession) -> AsyncGenerator[m.User, None]:
    """Create an admin user."""

    # Use unique email per test to avoid conflicts
    unique_id = str(uuid4())[:8]
    user = m.User(
        id=uuid4(),
        email=f"admin{unique_id}@example.com",
        name="Admin User",
        hashed_password=await get_password_hash("AdminPassword123!"),
        is_active=True,
        is_verified=True,
        is_superuser=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    yield user


@pytest.fixture
async def test_team(session: AsyncSession, test_user: m.User) -> AsyncGenerator[m.Team, None]:
    """Create a test team with owner."""
    # Use unique slug per test to avoid conflicts
    unique_id = str(uuid4())[:8]
    team = m.Team(
        id=uuid4(),
        name="Test Team",
        slug=f"test-team-{unique_id}",
        description="A test team for integration testing",
        is_active=True,
    )
    session.add(team)
    await session.commit()
    await session.refresh(team)

    # Add owner membership
    membership = m.TeamMember(
        team_id=team.id,
        user_id=test_user.id,
        role=m.TeamRoles.ADMIN,
        is_owner=True,
    )
    session.add(membership)
    await session.commit()

    yield team


@pytest.fixture
async def authenticated_client(client: AsyncTestClient, test_user: m.User) -> AsyncTestClient:
    """Create authenticated test client."""
    # Login and set auth headers
    login_response = await client.post(
        "/api/access/login", data={"username": test_user.email, "password": "TestPassword123!"}
    )

    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        client.headers.update({"Authorization": f"Bearer {token}"})

    return client


@pytest.fixture
async def admin_client(client: AsyncTestClient, admin_user: m.User) -> AsyncTestClient:
    """Create authenticated admin test client."""
    # Login as admin and set auth headers
    login_response = await client.post(
        "/api/access/login", data={"username": admin_user.email, "password": "AdminPassword123!"}
    )

    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        client.headers.update({"Authorization": f"Bearer {token}"})

    return client


# Service fixtures
@pytest.fixture
async def email_verification_service(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[EmailVerificationTokenService, None]:
    """Create EmailVerificationTokenService instance."""
    async with EmailVerificationTokenService.new(sessionmaker()) as service:
        yield service


@pytest.fixture
async def password_reset_service(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[PasswordResetService, None]:
    """Create PasswordResetService instance."""
    async with PasswordResetService.new(sessionmaker()) as service:
        yield service


@pytest.fixture
async def role_service(sessionmaker: async_sessionmaker[AsyncSession]) -> AsyncGenerator[RoleService, None]:
    """Create RoleService instance."""

    async with RoleService.new(sessionmaker()) as service:
        yield service


@pytest.fixture
async def tag_service(sessionmaker: async_sessionmaker[AsyncSession]) -> AsyncGenerator[TagService, None]:
    """Create TagService instance."""
    async with TagService.new(sessionmaker()) as service:
        yield service


@pytest.fixture
async def team_member_service(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[TeamMemberService, None]:
    """Create TeamMemberService instance."""

    async with TeamMemberService.new(sessionmaker()) as service:
        yield service


@pytest.fixture
async def team_invitation_service(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[TeamInvitationService, None]:
    """Create TeamInvitationService instance."""

    async with TeamInvitationService.new(sessionmaker()) as service:
        yield service


@pytest.fixture
async def user_role_service(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[UserRoleService, None]:
    """Create UserRoleService instance."""

    async with UserRoleService.new(sessionmaker()) as service:
        yield service


@pytest.fixture
async def user_oauth_service(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[UserOAuthAccountService, None]:
    """Create UserOAuthAccountService instance."""

    async with UserOAuthAccountService.new(sessionmaker()) as service:
        yield service


@pytest.fixture
def email_service() -> EmailService:
    """Create EmailService instance for testing."""

    return EmailService()


# Test data fixtures
@pytest.fixture
async def unverified_user(session: AsyncSession) -> m.User:
    """Create an unverified user."""

    user = m.User(
        id=uuid4(),
        email="unverified@example.com",
        name="Unverified User",
        hashed_password=await get_password_hash("TestPassword123!"),
        is_active=True,
        is_verified=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def inactive_user(session: AsyncSession) -> m.User:
    """Create an inactive user."""

    user = m.User(
        id=uuid4(),
        email="inactive@example.com",
        name="Inactive User",
        hashed_password=await get_password_hash("TestPassword123!"),
        is_active=False,
        is_verified=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def test_role(session: AsyncSession) -> m.Role:
    """Create a test role."""
    role = m.Role(
        id=uuid4(),
        name="test_role",
        slug="test-role",
        description="A test role for testing",
    )
    session.add(role)
    await session.commit()
    await session.refresh(role)
    return role


@pytest.fixture
async def test_tag(session: AsyncSession) -> m.Tag:
    """Create a test tag."""
    tag = m.Tag(
        id=uuid4(),
        name="test_tag",
        slug="test-tag",
        description="A test tag for testing",
    )
    session.add(tag)
    await session.commit()
    await session.refresh(tag)
    return tag


@pytest.fixture
async def test_verification_token(session: AsyncSession, unverified_user: m.User) -> m.EmailVerificationToken:
    """Create a test email verification token."""
    raw_token = uuid4().hex
    token = m.EmailVerificationToken(
        id=uuid4(),
        user_id=unverified_user.id,
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
        email=unverified_user.email,
        expires_at=datetime.now(UTC) + timedelta(hours=24),
    )
    token.raw_token = raw_token
    session.add(token)
    await session.commit()
    await session.refresh(token)
    return token


@pytest.fixture
async def test_password_reset_token(session: AsyncSession, test_user: m.User) -> m.PasswordResetToken:
    """Create a test password reset token."""

    raw_token = uuid4().hex
    token = m.PasswordResetToken(
        id=uuid4(),
        user_id=test_user.id,
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        ip_address="127.0.0.1",
        user_agent="Test User Agent",
    )
    token.raw_token = raw_token
    session.add(token)
    await session.commit()
    await session.refresh(token)
    return token


@pytest.fixture
async def test_oauth_account(session: AsyncSession, test_user: m.User) -> m.UserOAuthAccount:
    """Create a test OAuth account."""

    oauth_account = m.UserOAuthAccount(
        id=uuid4(),
        user_id=test_user.id,
        provider="google",
        oauth_id="test_oauth_id",
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        token_expires_at=datetime.now(UTC) + timedelta(hours=1),
        scope="openid email profile",
        provider_user_data={
            "email": test_user.email,
            "name": test_user.name,
            "picture": "https://example.com/avatar.jpg",
        },
        last_login_at=datetime.now(UTC),
    )
    session.add(oauth_account)
    await session.commit()
    await session.refresh(oauth_account)
    return oauth_account


@pytest.fixture
async def test_team_invitation(session: AsyncSession, test_team: m.Team, test_user: m.User) -> m.TeamInvitation:
    """Create a test team invitation."""
    invitation = m.TeamInvitation(
        id=uuid4(),
        team_id=test_team.id,
        email="invite@example.com",
        role=m.TeamRoles.MEMBER,
        is_accepted=False,
        invited_by_id=test_user.id,
        invited_by_email=test_user.email,
    )
    session.add(invitation)
    await session.commit()
    await session.refresh(invitation)
    return invitation
