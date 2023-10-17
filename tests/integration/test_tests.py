from typing import TYPE_CHECKING, cast

import pytest
from httpx import AsyncClient
from litestar import get
from sqlalchemy.ext.asyncio import AsyncSession

from app.lib import db

if TYPE_CHECKING:
    from litestar import Litestar
    from litestar.stores.redis import RedisStore
    from redis.asyncio import Redis as AsyncRedis
    from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker


def test_cache_on_app(app: "Litestar", redis: "AsyncRedis") -> None:
    """Test that the app's cache is patched.

    Args:
        app: The test Litestar instance
        redis: The test Redis client instance.
    """
    assert cast("RedisStore", app.stores.get("response_cache"))._redis is redis


def test_engine_on_app(app: "Litestar", engine: "AsyncEngine") -> None:
    """Test that the app's engine is patched.

    Args:
        app: The test Litestar instance
        engine: The test SQLAlchemy engine instance.
    """
    assert app.state[db.config.engine_app_state_key] is engine


def test_sessionmaker(app: "Litestar", sessionmaker: "async_sessionmaker[AsyncSession]") -> None:
    """Test that the sessionmaker is patched.

    Args:
        app: The test Litestar instance
        sessionmaker: The test SQLAlchemy sessionmaker factory.
    """
    assert db.async_session_factory is sessionmaker
    assert db.base.async_session_factory is sessionmaker


@pytest.mark.anyio
async def test_db_session_dependency(app: "Litestar", engine: "AsyncEngine") -> None:
    """Test that handlers receive session attached to patched engine.

    Args:
        app: The test Litestar instance
        engine: The patched SQLAlchemy engine instance.
    """

    @get("/db-session-test", opt={"exclude_from_auth": True})
    async def db_session_dependency_patched(db_session: AsyncSession) -> dict[str, str]:
        return {"result": f"{db_session.bind is engine = }"}

    app.register(db_session_dependency_patched)
    # can't use test client as it always starts its own event loop
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/db-session-test")
        assert response.json()["result"] == "db_session.bind is engine = True"
