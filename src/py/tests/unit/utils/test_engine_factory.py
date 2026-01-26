from unittest.mock import MagicMock

from sqlalchemy.ext.asyncio import AsyncEngine

from app.utils.engine_factory import create_sqlalchemy_engine


def test_create_sqlalchemy_engine_psycopg() -> None:
    settings = MagicMock()
    settings.URL = "postgresql+psycopg://user:pass@localhost/db"
    settings.ECHO = False
    settings.ECHO_POOL = False
    settings.POOL_RECYCLE = 300
    settings.POOL_PRE_PING = False
    settings.POOL_DISABLED = False
    settings.POOL_MAX_OVERFLOW = 10
    settings.POOL_SIZE = 5
    settings.POOL_TIMEOUT = 30

    engine = create_sqlalchemy_engine(settings)
    assert isinstance(engine, AsyncEngine)
    assert engine.url.drivername == "postgresql+psycopg"
    assert engine.url.username == "user"
    assert engine.url.password == "pass"


def test_create_sqlalchemy_engine_sqlite() -> None:
    settings = MagicMock()
    settings.URL = "sqlite+aiosqlite:///test.db"
    settings.ECHO = False
    settings.ECHO_POOL = False
    settings.POOL_RECYCLE = 300
    settings.POOL_PRE_PING = False

    engine = create_sqlalchemy_engine(settings)
    assert isinstance(engine, AsyncEngine)
    assert engine.url.drivername == "sqlite+aiosqlite"
    assert engine.url.database == "test.db"


def test_create_sqlalchemy_engine_asyncpg() -> None:
    settings = MagicMock()
    settings.URL = "postgresql+asyncpg://user:pass@localhost/db"
    settings.ECHO = False
    settings.ECHO_POOL = False
    settings.POOL_RECYCLE = 300
    settings.POOL_PRE_PING = False
    settings.POOL_DISABLED = False
    settings.POOL_MAX_OVERFLOW = 10
    settings.POOL_SIZE = 5
    settings.POOL_TIMEOUT = 30

    engine = create_sqlalchemy_engine(settings)
    assert isinstance(engine, AsyncEngine)
    assert engine.url.drivername == "postgresql+asyncpg"
    assert engine.url.username == "user"
    assert engine.url.password == "pass"


def test_create_sqlalchemy_engine_null_pool() -> None:
    settings = MagicMock()
    settings.URL = "postgresql+psycopg://user:pass@localhost/db"
    settings.POOL_DISABLED = True
    settings.ECHO = False
    settings.ECHO_POOL = False
    settings.POOL_RECYCLE = 300
    settings.POOL_PRE_PING = False

    engine = create_sqlalchemy_engine(settings)
    assert isinstance(engine, AsyncEngine)
    # We can't easily check the pool class without more introspection,
    # but we can ensure it doesn't crash.
