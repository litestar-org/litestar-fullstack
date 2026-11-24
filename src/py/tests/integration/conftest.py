"""PostgreSQL integration test fixtures using cookie sessions, CSRF, and template-cloned databases."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from advanced_alchemy.utils.fixtures import open_fixture_async
from litestar import Litestar
from litestar.testing import AsyncTestClient
from litestar_email import EmailConfig
from litestar_security.accounts import Argon2PasswordHasher
from sqlalchemy import select

from app import config
from app.db import models as m
from app.domain.accounts.security.config import build_security_config
from app.domain.accounts.services import RoleService, UserService
from app.domain.teams.services import TeamService
from app.lib.settings import get_settings
from app.server.core import ApplicationCore

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, AsyncIterator

    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

pytestmark = pytest.mark.anyio

_PASSWORD_HASHER = Argon2PasswordHasher()
CSRF_COOKIE_NAME = "XSRF-TOKEN"
CSRF_HEADER_NAME = "X-XSRF-TOKEN"


def reset_client_session(client: AsyncClient) -> None:
    """Clear cookies and auth/CSRF headers so one client can switch principals cleanly."""
    client.cookies.clear()
    client.headers.pop(CSRF_HEADER_NAME, None)
    client.headers.pop("Authorization", None)


async def fetch_csrf_headers(client: AsyncClient) -> dict[str, str]:
    """Ensure the client holds a CSRF cookie and return matching request headers."""
    token = client.cookies.get(CSRF_COOKIE_NAME)
    if not token:
        await client.get("/api/config/auth")
        token = client.cookies.get(CSRF_COOKIE_NAME)
    return {CSRF_HEADER_NAME: token} if token else {}


async def login_session_client(
    client: AsyncClient,
    email: str,
    password: str,
) -> dict[str, str]:
    """Authenticate via LocalAuth.session cookie flow and return CSRF headers for mutating requests."""
    csrf_headers = await fetch_csrf_headers(client)
    response = await client.post(
        "/api/access/login",
        json={"identifier": email, "password": password},
        headers=csrf_headers,
    )
    assert response.status_code == 200, f"Login failed ({response.status_code}): {response.text}"
    return await fetch_csrf_headers(client)


@pytest.fixture
async def seeded_db(
    sessionmaker: async_sessionmaker[AsyncSession],
    raw_users: list[m.User | dict[str, Any]],
    raw_teams: list[m.Team | dict[str, Any]],
    db_cleanup: None,
) -> AsyncGenerator[None, None]:
    """Populate the worker PostgreSQL database with roles, users, and teams."""
    _ = db_cleanup
    settings = get_settings()
    fixtures_path = Path(settings.db.FIXTURE_PATH)
    async with RoleService.new(sessionmaker()) as service:
        fixture = await open_fixture_async(fixtures_path, "role")
        for obj in fixture:
            _ = await service.repository.get_or_upsert(match_fields="name", upsert=True, **obj)
        await service.repository.session.commit()
    async with UserService.new(sessionmaker(), load=[m.User.teams]) as users_service:
        await users_service.create_many(raw_users, auto_commit=True)
    async with TeamService.new(sessionmaker(), load=[m.Team.members, m.Team.tags]) as teams_service:
        for obj in raw_teams:
            await teams_service.create(obj)
        await teams_service.repository.session.commit()
    yield


@pytest.fixture
def _patch_db(
    engine: AsyncEngine,
    sessionmaker: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bind the shared SQLAlchemyAsyncConfig singleton to the worker PostgreSQL engine."""
    monkeypatch.setattr(config.alchemy, "session_maker", sessionmaker)
    monkeypatch.setattr(config.alchemy, "engine_instance", engine)
    monkeypatch.setattr(config.alchemy, "connection_string", engine.url.render_as_string(hide_password=False))


@pytest.fixture(name="app")
def fx_app(
    engine: AsyncEngine,
    sessionmaker: async_sessionmaker[AsyncSession],
    db_schema: None,
    _patch_db: None,
) -> Litestar:
    """Build a fresh Litestar application bound to the worker PostgreSQL database."""
    _ = (db_schema, _patch_db)
    settings = get_settings()
    queue_config = settings.queues.get_config(
        alchemy_config=config.alchemy,
        db_settings=settings.db,
        app_settings=settings.app,
    )
    security_config = build_security_config(settings, config.alchemy)
    app_instance = Litestar(
        plugins=[
            ApplicationCore(
                security_config=security_config,
                queue_config=queue_config,
                email_config=EmailConfig(backend="memory"),
            )
        ]
    )
    app_instance.state[config.alchemy.engine_app_state_key] = engine
    app_instance.state[config.alchemy.session_maker_app_state_key] = sessionmaker
    return app_instance


@pytest.fixture(name="client")
async def fx_client(app: Litestar, db_cleanup: None) -> AsyncIterator[AsyncClient]:
    """Unauthenticated AsyncTestClient connected to the integration app."""
    _ = db_cleanup
    async with AsyncTestClient(app=app) as client:
        yield client


@pytest.fixture(name="seeded_client")
async def fx_seeded_client(
    app: Litestar,
    seeded_db: None,
    db_cleanup: None,
) -> AsyncIterator[AsyncClient]:
    """Unauthenticated AsyncTestClient with seeded users, roles, and teams."""
    _ = (seeded_db, db_cleanup)
    async with AsyncTestClient(app=app) as client:
        yield client


@pytest.fixture(name="test_user")
async def fx_test_user(
    session: AsyncSession,
    _patch_db: None,
    db_cleanup: None,
) -> m.User:
    """Create a verified, active regular user with an Argon2 password hash."""
    _ = (_patch_db, db_cleanup)
    user = m.User(
        email="authuser@example.com",
        name="Auth Test User",
        hashed_password=await _PASSWORD_HASHER.hash("TestPassword123!"),
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
) -> m.User:
    """Create an inactive user for login rejection tests."""
    _ = (_patch_db, db_cleanup)
    user = m.User(
        email="inactive.auth@example.com",
        name="Inactive Auth User",
        hashed_password=await _PASSWORD_HASHER.hash("TestPassword123!"),
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
) -> m.User:
    """Create an unverified user for email verification tests."""
    _ = (_patch_db, db_cleanup)
    user = m.User(
        email="unverified.auth@example.com",
        name="Unverified Auth User",
        hashed_password=await _PASSWORD_HASHER.hash("TestPassword123!"),
        is_active=True,
        is_verified=False,
        is_superuser=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture(name="authenticated_client")
async def fx_authenticated_client(
    client: AsyncClient,
    test_user: m.User,
) -> AsyncClient:
    """AsyncTestClient authenticated as ``test_user`` via cookie session with default CSRF header."""
    csrf_headers = await login_session_client(client, test_user.email, "TestPassword123!")
    client.headers.update(csrf_headers)
    return client


@pytest.fixture(name="superuser_client")
async def fx_superuser_client(
    seeded_client: AsyncClient,
) -> AsyncClient:
    """AsyncTestClient authenticated as seeded superuser via cookie session with default CSRF header."""
    csrf_headers = await login_session_client(seeded_client, "superuser@example.com", "Test_Password1!")
    seeded_client.headers.update(csrf_headers)
    return seeded_client


@pytest.fixture(name="api_key_headers")
async def fx_api_key_headers(
    authenticated_client: AsyncClient,
) -> dict[str, str]:
    """Issue a personal API key through ``POST /api/me/api-keys`` and return Bearer auth headers."""
    response = await authenticated_client.post(
        "/api/me/api-keys",
        json={"name": "Integration Key", "scopes": ["read", "write", "mcp"]},
    )
    assert response.status_code == 201, f"API key creation failed: {response.text}"
    secret = response.json()["secret"]
    return {"Authorization": f"Bearer {secret}"}


@pytest.fixture(name="test_team")
async def fx_test_team(
    session: AsyncSession,
    test_user: m.User,
    _patch_db: None,
) -> m.Team:
    """Create a test team owned by ``test_user``."""
    _ = _patch_db
    team = m.Team(
        name="Auth Test Team",
        slug="auth-test-team",
        description="Test team for integration tests",
        is_active=True,
    )
    session.add(team)
    await session.flush()

    membership = m.TeamMember(
        team_id=team.id,
        user_id=test_user.id,
        role=m.TeamRoles.ADMIN,
        is_owner=True,
    )
    session.add(membership)
    await session.commit()
    await session.refresh(team, ["members"])
    return team


@pytest.fixture(name="test_team_member")
async def fx_test_team_member(
    session: AsyncSession,
    test_team: m.Team,
    _patch_db: None,
) -> m.User:
    """Create a regular ``MEMBER`` user belonging to ``test_team``."""
    _ = _patch_db
    user = m.User(
        email="teammember@example.com",
        name="Team Member User",
        hashed_password=await _PASSWORD_HASHER.hash("TestPassword123!"),
        is_active=True,
        is_verified=True,
        is_superuser=False,
    )
    session.add(user)
    await session.flush()

    membership = m.TeamMember(
        team_id=test_team.id,
        user_id=user.id,
        role=m.TeamRoles.MEMBER,
        is_owner=False,
    )
    session.add(membership)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture(name="test_team_invitation")
async def fx_test_team_invitation(
    session: AsyncSession,
    test_team: m.Team,
    test_user: m.User,
    _patch_db: None,
) -> m.TeamInvitation:
    """Create a pending team invitation for ``test_team``."""
    _ = _patch_db
    invitation = m.TeamInvitation(
        team_id=test_team.id,
        email="invited.user@example.com",
        role=m.TeamRoles.MEMBER,
        is_accepted=False,
        invited_by_id=test_user.id,
        invited_by_email=test_user.email,
    )
    session.add(invitation)
    await session.commit()
    await session.refresh(invitation)
    return invitation


async def get_user_by_email(session: AsyncSession, email: str) -> m.User | None:
    """Query a user by email from the provided session."""
    return await session.scalar(select(m.User).where(m.User.email == email))
