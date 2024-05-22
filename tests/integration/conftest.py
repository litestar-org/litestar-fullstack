from collections.abc import AsyncGenerator, AsyncIterator
from pathlib import Path
from typing import Any

import pytest
from advanced_alchemy.base import UUIDAuditBase
from advanced_alchemy.utils.fixtures import open_fixture_async
from httpx import AsyncClient
from litestar import Litestar
from litestar_saq.cli import get_saq_plugin
from redis.asyncio import Redis
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.db.models import Team, User
from app.domain.accounts.guards import auth
from app.domain.accounts.services import RoleService, UserService
from app.domain.teams.services import TeamService
from app.server.builder import ApplicationConfigurator
from app.server.plugins import alchemy

here = Path(__file__).parent
pytestmark = pytest.mark.anyio


@pytest.fixture(name="engine", autouse=True)
async def fx_engine(
    postgres_docker_ip: str,
    postgres_service: None,
    redis_service: None,
    postgres_port: int,
    postgres_user: str,
    postgres_password: str,
    postgres_database: str,
) -> AsyncEngine:
    """Postgresql instance for end-to-end testing.

    Returns:
        Async SQLAlchemy engine instance.
    """
    return create_async_engine(
        URL(
            drivername="postgresql+asyncpg",
            username=postgres_user,
            password=postgres_password,
            host=postgres_docker_ip,
            port=postgres_port,
            database=postgres_database,
            query={},  # type:ignore[arg-type]
        ),
        echo=False,
        poolclass=NullPool,
    )


@pytest.fixture(name="sessionmaker")
def fx_session_maker_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture(name="session")
async def fx_session(sessionmaker: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    async with sessionmaker() as session:
        yield session


@pytest.fixture(autouse=True)
async def _seed_db(
    engine: AsyncEngine,
    sessionmaker: async_sessionmaker[AsyncSession],
    raw_users: list[User | dict[str, Any]],
    raw_teams: list[Team | dict[str, Any]],
) -> AsyncIterator[None]:
    """Populate test database with.

    Args:
        engine: The SQLAlchemy engine instance.
        sessionmaker: The SQLAlchemy sessionmaker factory.
        raw_users: Test users to add to the database
        raw_teams: Test teams to add to the database

    """

    settings = get_settings()
    fixtures_path = Path(settings.db.FIXTURE_PATH)
    metadata = UUIDAuditBase.registry.metadata
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)
    async with RoleService.new(sessionmaker()) as service:
        fixture = await open_fixture_async(fixtures_path, "role")
        for obj in fixture:
            _ = await service.repository.get_or_upsert(match_fields="name", upsert=True, **obj)
        await service.repository.session.commit()
    async with UserService.new(sessionmaker()) as users_service:
        await users_service.create_many(raw_users, auto_commit=True)
    async with TeamService.new(sessionmaker()) as teams_services:
        for obj in raw_teams:
            await teams_services.create(obj)
        await teams_services.repository.session.commit()

    yield


@pytest.fixture(autouse=True)
def _patch_db(
    app: "Litestar",
    engine: AsyncEngine,
    sessionmaker: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(alchemy._config, "session_maker", sessionmaker)
    monkeypatch.setitem(app.state, alchemy._config.engine_app_state_key, engine)
    monkeypatch.setitem(
        app.state,
        alchemy._config.session_maker_app_state_key,
        async_sessionmaker(bind=engine, expire_on_commit=False),
    )


@pytest.fixture(autouse=True)
def _patch_redis(app: "Litestar", redis: Redis, monkeypatch: pytest.MonkeyPatch) -> None:
    cache_config = app.response_cache_config
    assert cache_config is not None
    saq_plugin = get_saq_plugin(app)
    app_plugin = app.plugins.get(ApplicationConfigurator)
    monkeypatch.setattr(app_plugin, "redis", redis)
    monkeypatch.setattr(app.stores.get(cache_config.store), "_redis", redis)
    if saq_plugin._config.queue_instances is not None:
        for queue in saq_plugin._config.queue_instances.values():
            monkeypatch.setattr(queue, "redis", redis)


@pytest.fixture(name="client")
async def fx_client(app: Litestar) -> AsyncIterator[AsyncClient]:
    """Async client that calls requests on the app.

    ```text
    ValueError: The future belongs to a different loop than the one specified as the loop argument
    ```
    """
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest.fixture(name="superuser_token_headers")
def fx_superuser_token_headers() -> dict[str, str]:
    """Valid superuser token.

    ```text
    ValueError: The future belongs to a different loop than the one specified as the loop argument
    ```
    """
    return {"Authorization": f"Bearer {auth.create_token(identifier='superuser@example.com')}"}


@pytest.fixture(name="user_token_headers")
def fx_user_token_headers() -> dict[str, str]:
    """Valid user token.

    ```text
    ValueError: The future belongs to a different loop than the one specified as the loop argument
    ```
    """
    return {"Authorization": f"Bearer {auth.create_token(identifier='user@example.com')}"}
