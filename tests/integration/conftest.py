import os
import sys
from collections.abc import AsyncGenerator, AsyncIterator, Generator
from pathlib import Path
from typing import Any

import pytest
from httpx import AsyncClient
from litestar import Litestar
from litestar_saq.cli import get_saq_plugin
from redis.asyncio import Redis
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.domain.accounts.models import User
from app.domain.security import auth
from app.domain.teams.models import Team
from app.lib import db
from tests.docker_service import DockerServiceRegistry, postgres_responsive, redis_responsive

here = Path(__file__).parent


@pytest.fixture(scope="session")
def docker_services() -> Generator[DockerServiceRegistry, None, None]:
    if sys.platform not in ("linux", "darwin") or os.environ.get("SKIP_DOCKER_TESTS"):
        pytest.skip("Docker not available on this platform")

    registry = DockerServiceRegistry()
    try:
        yield registry
    finally:
        registry.down()


@pytest.fixture(scope="session")
def docker_ip(docker_services: DockerServiceRegistry) -> str:
    return docker_services.docker_ip


@pytest.fixture()
async def postgres_service(docker_services: DockerServiceRegistry) -> None:
    await docker_services.start("postgres", check=postgres_responsive)


@pytest.fixture()
async def redis_service(docker_services: DockerServiceRegistry) -> None:
    await docker_services.start("redis", check=redis_responsive)


@pytest.fixture(name="engine")
async def fx_engine(docker_ip: str, postgres_service: None) -> AsyncEngine:
    """Postgresql instance for end-to-end testing.

    Args:
        docker_ip: IP address for TCP connection to Docker containers.
        postgres_service: docker service
    Returns:
        Async SQLAlchemy engine instance.
    """
    return create_async_engine(
        URL(
            drivername="postgresql+asyncpg",
            username="postgres",
            password="super-secret",  # noqa: S106
            host=docker_ip,
            port=5423,
            database="postgres",
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

    from app.domain.accounts.services import UserService
    from app.domain.teams.services import TeamService
    from app.lib.db import orm  # pylint: disable=[import-outside-toplevel,unused-import]

    metadata = orm.DatabaseModel.registry.metadata
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)
    async with UserService.new(sessionmaker()) as users_service:
        await users_service.create_many(raw_users)
        await users_service.repository.session.commit()
    async with TeamService.new(sessionmaker()) as teams_services:
        for raw_team in raw_teams:
            await teams_services.create(raw_team)
        await teams_services.repository.session.commit()

    return None  # type: ignore[return-value]


@pytest.fixture(autouse=True)
def _patch_db(
    app: "Litestar",
    engine: AsyncEngine,
    sessionmaker: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(db, "async_session_factory", sessionmaker)
    monkeypatch.setattr(db.base, "async_session_factory", sessionmaker)
    monkeypatch.setitem(app.state, db.config.engine_app_state_key, engine)
    monkeypatch.setitem(
        app.state,
        db.config.session_maker_app_state_key,
        async_sessionmaker(bind=engine, expire_on_commit=False),
    )


@pytest.fixture(name="redis")
async def fx_redis(docker_ip: str, redis_service: None) -> Redis:
    """Redis instance for testing.

    Args:
        docker_ip: IP of docker host.
        redis_service: docker service

    Returns:
        Redis client instance, function scoped.
    """
    return Redis(host=docker_ip, port=6397)


@pytest.fixture(autouse=True)
def _patch_redis(app: "Litestar", redis: Redis, monkeypatch: pytest.MonkeyPatch) -> None:
    cache_config = app.response_cache_config
    assert cache_config is not None
    saq_plugin = get_saq_plugin(app)
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
