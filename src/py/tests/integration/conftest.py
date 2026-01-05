from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from advanced_alchemy.utils.fixtures import open_fixture_async
from litestar.testing import AsyncTestClient

from app import config
from app.db.models import Team, User
from app.domain.accounts.guards import create_access_token
from app.domain.accounts.services import RoleService, UserService
from app.domain.teams.services import TeamService
from app.lib.settings import get_settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, AsyncIterator

    from httpx import AsyncClient
    from litestar import Litestar
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

pytestmark = pytest.mark.anyio


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


@pytest.fixture(autouse=True)
async def _patch_db(
    app: Litestar,
    engine: AsyncEngine,
    sessionmaker: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Patch the database connection for integration tests.

    This fixture ensures that all HTTP requests made through the test client
    use the same test database that fixtures populate.
    """
    monkeypatch.setattr(config.alchemy, "session_maker", sessionmaker)
    monkeypatch.setattr(config.alchemy, "engine_instance", engine)
    # Also patch app state for tests that check app.state directly
    app.state[config.alchemy.engine_app_state_key] = engine
    app.state[config.alchemy.session_maker_app_state_key] = sessionmaker


@pytest.fixture(name="client")
async def fx_client(app: Litestar, db_cleanup: None) -> AsyncIterator[AsyncClient]:
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
