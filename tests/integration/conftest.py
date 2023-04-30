import asyncio
import timeit
from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

import asyncpg
import pytest
from httpx import AsyncClient
from litestar import Litestar
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.domain.accounts.models import User
from app.domain.security import auth
from app.domain.teams.models import Team
from app.lib import db, worker

if TYPE_CHECKING:
    from collections import abc

    from pytest_docker.plugin import Services


here = Path(__file__).parent


@pytest.fixture(scope="session")
def event_loop() -> "abc.Iterator[asyncio.AbstractEventLoop]":
    """Scoped Event loop.

    Need the event loop scoped to the session so that we can use it to check
    containers are ready in session scoped containers fixture.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def docker_compose_file() -> Path:
    """Load docker compose file.

    Returns:
        Path to the docker-compose file for end-to-end test environment.
    """
    return here / "docker-compose.yml"


async def wait_until_responsive(
    check: "abc.Callable[..., abc.Awaitable]",
    timeout: float,
    pause: float,
    **kwargs: Any,
) -> None:
    """Wait until a service is responsive.

    Args:
        check: Coroutine, return truthy value when waiting should stop.
        timeout: Maximum seconds to wait.
        pause: Seconds to wait between calls to `check`.
        **kwargs: Given as kwargs to `check`.
    """
    ref = timeit.default_timer()
    now = ref
    while (now - ref) < timeout:
        if await check(**kwargs):
            return
        await asyncio.sleep(pause)
        now = timeit.default_timer()

    raise Exception("Timeout reached while waiting on service!")


async def redis_responsive(host: str) -> bool:
    """Args:
        host: docker IP address.

    Returns:
        Boolean indicating if we can connect to the redis server.
    """
    client: Redis = Redis(host=host, port=6397)
    try:
        return await client.ping()
    except (ConnectionError, RedisConnectionError):
        return False
    finally:
        await client.close()


async def db_responsive(host: str) -> bool:
    """Args:
        host: docker IP address.

    Returns:
        Boolean indicating if we can connect to the database.
    """
    try:
        conn = await asyncpg.connect(
            host=host,
            port=5423,
            user="postgres",
            database="postgres",
            password="super-secret",  # noqa: S106
        )
    except (ConnectionError, asyncpg.CannotConnectNowError):
        return False

    try:
        return (await conn.fetchrow("SELECT 1"))[0] == 1  # type:ignore[index,no-any-return]
    finally:
        await conn.close()


@pytest.fixture(scope="session", autouse=True)
async def _containers(docker_ip: str, docker_services: "Services") -> None:  # pylint: disable=unused-argument
    """Starts containers for required services, fixture waits until they are
    responsive before returning.

    Args:
        docker_ip: the test docker IP
        docker_services: the test docker services
    """
    await wait_until_responsive(timeout=30.0, pause=0.1, check=db_responsive, host=docker_ip)
    await wait_until_responsive(timeout=30.0, pause=0.1, check=redis_responsive, host=docker_ip)


@pytest.fixture(name="redis")
async def fx_redis(docker_ip: str) -> Redis:
    """Redis instance for testing.

    Args:
        docker_ip: IP of docker host.

    Returns:
        Redis client instance, function scoped.
    """
    return Redis(host=docker_ip, port=6397)


@pytest.fixture(name="engine")
async def fx_engine(docker_ip: str) -> AsyncEngine:
    """Postgresql instance for end-to-end testing.

    Args:
        docker_ip: IP address for TCP connection to Docker containers.

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
def fx_session(sessionmaker: async_sessionmaker[AsyncSession]) -> AsyncSession:
    return sessionmaker()


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
        await teams_services.create_many(raw_teams)
        await teams_services.repository.session.commit()

    yield


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


@pytest.fixture(autouse=True)
def _patch_redis(app: "Litestar", redis: Redis, monkeypatch: pytest.MonkeyPatch) -> None:
    cache_config = app.response_cache_config
    assert cache_config is not None
    monkeypatch.setattr(app.stores.get(cache_config.store), "_redis", redis)
    monkeypatch.setattr(worker.queue, "redis", redis)


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
