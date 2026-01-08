from __future__ import annotations

from datetime import UTC
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from advanced_alchemy.utils.fixtures import open_fixture_async
from litestar.testing import AsyncTestClient

from app import config
from app.db.models import EmailVerificationToken, PasswordResetToken, Team, TeamInvitation, User
from app.domain.accounts.guards import create_access_token
from app.domain.accounts.services import RoleService, UserService
from app.domain.teams.services import TeamService
from app.lib.settings import get_settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, AsyncIterator

    from httpx import AsyncClient
    from litestar import Litestar
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


@pytest.fixture
async def seeded_db(
    sessionmaker: async_sessionmaker[AsyncSession],
    raw_users: list[User | dict[str, Any]],
    raw_teams: list[Team | dict[str, Any]],
    db_cleanup: None,
) -> AsyncGenerator[None, None]:
    """Populate test database with fixtures when explicitly requested.

    Args:
        sessionmaker: The SQLAlchemy sessionmaker factory.
        raw_users: Test users to add to the database
        raw_teams: Test teams to add to the database
        db_cleanup: Per-test cleanup dependency to ensure isolation.

    """

    settings = get_settings()
    fixtures_path = Path(settings.db.FIXTURE_PATH)
    async with RoleService.new(sessionmaker()) as service:
        fixture = await open_fixture_async(fixtures_path, "role")
        for obj in fixture:
            _ = await service.repository.get_or_upsert(match_fields="name", upsert=True, **obj)
        await service.repository.session.commit()
    async with UserService.new(sessionmaker(), load=[User.teams]) as users_service:
        await users_service.create_many(raw_users, auto_commit=True)
    async with TeamService.new(sessionmaker(), load=[Team.members, Team.tags]) as teams_services:
        for obj in raw_teams:
            await teams_services.create(obj)
        await teams_services.repository.session.commit()

    yield


@pytest.fixture
async def _patch_db(
    app: Litestar,
    engine: AsyncEngine,
    sessionmaker: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Patch the database connection for HTTP client tests.

    This fixture ensures that all HTTP requests made through the test client
    use the same test database that fixtures populate.

    Note: This is NOT autouse - only client tests need it.
    Service tests use session directly and don't need app patching.
    """
    monkeypatch.setattr(config.alchemy, "session_maker", sessionmaker)
    monkeypatch.setattr(config.alchemy, "engine_instance", engine)
    # Also patch app state for tests that check app.state directly
    app.state[config.alchemy.engine_app_state_key] = engine
    app.state[config.alchemy.session_maker_app_state_key] = sessionmaker


@pytest.fixture(name="client")
async def fx_client(app: Litestar, _patch_db: None, db_cleanup: None) -> AsyncIterator[AsyncClient]:
    """Async client that calls requests on the app."""
    async with AsyncTestClient(app) as client:
        yield client


@pytest.fixture(name="superuser_token_headers")
def fx_superuser_token_headers(seeded_db: None) -> dict[str, str]:
    """Valid superuser token."""
    token = create_access_token(
        user_id="superuser",
        email="superuser@example.com",
        is_superuser=True,
        is_verified=True,
        auth_method="password",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(name="user_token_headers")
def fx_user_token_headers(seeded_db: None) -> dict[str, str]:
    """Valid user token."""
    token = create_access_token(
        user_id="user",
        email="user@example.com",
        is_superuser=False,
        is_verified=True,
        auth_method="password",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(name="seeded_client")
async def fx_seeded_client(
    app: Litestar,
    _patch_db: None,
    seeded_db: None,
    db_cleanup: None,
) -> AsyncIterator[AsyncClient]:
    """Async client with seeded database.

    Uses _patch_db to ensure the test client uses the same database
    that was seeded with fixtures.
    """
    async with AsyncTestClient(app=app) as client:
        yield client


@pytest.fixture(name="authenticated_client")
async def fx_authenticated_client(
    client: AsyncClient,
    test_user: User,
) -> AsyncClient:
    """Client with authentication headers for test_user.

    Logs in the test_user and returns the client ready to make authenticated requests.
    """
    # Login and get token
    login_response = await client.post(
        "/api/access/login",
        data={"username": test_user.email, "password": "TestPassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 201, f"Login failed: {login_response.text}"
    token = login_response.json()["access_token"]

    # Set auth header on client
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture(name="test_user")
async def fx_test_user(
    session: AsyncSession,
    _patch_db: None,
    db_cleanup: None,
) -> User:
    """Create a test user for authentication tests.

    Returns a verified, active user with a known password.
    Note: Email cannot start with 'test' due to validation rules.
    """
    from app.lib.crypt import get_password_hash

    user = User(
        email="authuser@example.com",
        name="Auth Test User",
        hashed_password=await get_password_hash("TestPassword123!"),
        is_active=True,
        is_verified=True,
        is_superuser=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture(name="inactive_user")
async def fx_inactive_user(
    session: AsyncSession,
    _patch_db: None,
    db_cleanup: None,
) -> User:
    """Create an inactive user for testing login failures.

    Note: Email cannot start with 'test' due to validation rules.
    """
    from app.lib.crypt import get_password_hash

    user = User(
        email="inactive.auth@example.com",
        name="Inactive Auth User",
        hashed_password=await get_password_hash("TestPassword123!"),
        is_active=False,
        is_verified=True,
        is_superuser=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture(name="unverified_user")
async def fx_unverified_user(
    session: AsyncSession,
    _patch_db: None,
    db_cleanup: None,
) -> User:
    """Create an unverified user for email verification tests.

    Note: Email cannot start with 'test' due to validation rules.
    """
    from app.lib.crypt import get_password_hash

    user = User(
        email="unverified.auth@example.com",
        name="Unverified Auth User",
        hashed_password=await get_password_hash("TestPassword123!"),
        is_active=True,
        is_verified=False,
        is_superuser=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture(name="test_password_reset_token")
async def fx_test_password_reset_token(
    session: AsyncSession,
    test_user: User,
    _patch_db: None,
) -> PasswordResetToken:
    """Create a password reset token for testing."""
    import hashlib
    import secrets
    from datetime import datetime, timedelta

    raw_token = secrets.token_urlsafe(32)
    # Use SHA256 hash to match the service's verification method
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    token = PasswordResetToken(
        user_id=test_user.id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    # Store raw token for tests to use (get_raw_token expects raw_token attr)
    token.raw_token = raw_token  # type: ignore[attr-defined]
    session.add(token)
    await session.commit()
    await session.refresh(token)
    return token


@pytest.fixture(name="test_email_verification_token")
async def fx_test_email_verification_token(
    session: AsyncSession,
    test_user: User,
    _patch_db: None,
) -> EmailVerificationToken:
    """Create an email verification token for testing."""
    import hashlib
    import secrets
    from datetime import datetime, timedelta

    raw_token = secrets.token_urlsafe(32)
    # Use SHA256 hash to match the service's verification method
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    token = EmailVerificationToken(
        user_id=test_user.id,
        token_hash=token_hash,
        email=test_user.email,
        expires_at=datetime.now(UTC) + timedelta(hours=24),
    )
    # Store raw token for tests to use (get_raw_token expects raw_token attr)
    token.raw_token = raw_token  # type: ignore[attr-defined]
    session.add(token)
    await session.commit()
    await session.refresh(token)
    return token


@pytest.fixture(name="test_verification_token")
async def fx_test_verification_token(
    session: AsyncSession,
    unverified_user: User,
    _patch_db: None,
) -> EmailVerificationToken:
    """Create email verification token for unverified user."""
    import hashlib
    import secrets
    from datetime import datetime, timedelta

    raw_token = secrets.token_urlsafe(32)
    # Use SHA256 hash to match the service's verification method
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    token = EmailVerificationToken(
        user_id=unverified_user.id,
        token_hash=token_hash,
        email=unverified_user.email,
        expires_at=datetime.now(UTC) + timedelta(hours=24),
    )
    token.raw_token = raw_token  # type: ignore[attr-defined]
    session.add(token)
    await session.commit()
    await session.refresh(token)
    return token


@pytest.fixture(name="test_team")
async def fx_test_team(
    session: AsyncSession,
    test_user: User,
    _patch_db: None,
) -> Team:
    """Create a test team with test_user as owner."""
    from app.db.models import TeamMember, TeamRoles

    team = Team(
        name="Auth Test Team",
        slug="auth-test-team",
        description="Test team for authentication tests",
        is_active=True,
    )
    session.add(team)
    await session.flush()

    # Add test_user as owner
    membership = TeamMember(
        team_id=team.id,
        user_id=test_user.id,
        role=TeamRoles.ADMIN,
        is_owner=True,
    )
    session.add(membership)
    await session.commit()
    await session.refresh(team, ["members"])
    return team


@pytest.fixture(name="test_team_member")
async def fx_test_team_member(
    session: AsyncSession,
    test_team: Team,
    _patch_db: None,
) -> User:
    """Create another user who is a member of test_team."""
    from app.db.models import TeamMember, TeamRoles
    from app.lib.crypt import get_password_hash

    user = User(
        email="teammember@example.com",
        name="Team Member User",
        hashed_password=await get_password_hash("TestPassword123!"),
        is_active=True,
        is_verified=True,
        is_superuser=False,
    )
    session.add(user)
    await session.flush()

    membership = TeamMember(
        team_id=test_team.id,
        user_id=user.id,
        role=TeamRoles.MEMBER,
        is_owner=False,
    )
    session.add(membership)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture(name="test_team_invitation")
async def fx_test_team_invitation(
    session: AsyncSession,
    test_team: Team,
    test_user: User,
    _patch_db: None,
) -> TeamInvitation:
    """Create a team invitation for testing."""
    from app.db.models import TeamRoles

    invitation = TeamInvitation(
        team_id=test_team.id,
        email="invited.user@example.com",
        role=TeamRoles.MEMBER,
        is_accepted=False,
        invited_by_id=test_user.id,
        invited_by_email=test_user.email,
    )
    session.add(invitation)
    await session.commit()
    await session.refresh(invitation)
    return invitation
