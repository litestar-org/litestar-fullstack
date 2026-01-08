from __future__ import annotations

import os
from typing import TYPE_CHECKING

# Set test environment BEFORE any app imports (settings are cached on first import)
os.environ.update(
    {
        "SECRET_KEY": "secret-key",
        "DATABASE_ECHO": "false",
        "DATABASE_ECHO_POOL": "false",
        "SAQ_USE_SERVER_LIFESPAN": "False",
        "SAQ_WEB_ENABLED": "True",
        "SAQ_PROCESSES": "1",
        "SAQ_CONCURRENCY": "1",
        "VITE_PORT": "3006",
        "VITE_DEV_MODE": "True",
        "EMAIL_BACKEND": "memory",
        "LITESTAR_DEBUG": "False",
    }
)

# Now import app modules after environment is configured
import pytest
from advanced_alchemy.base import UUIDAuditBase
from litestar_email import EmailConfig, EmailService, InMemoryBackend
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from litestar import Litestar
    from pytest_databases.docker.postgres import PostgresService
    from sqlalchemy.ext.asyncio import AsyncEngine


pytest_plugins = [
    "tests.data_fixtures",
    "pytest_databases.docker",
    "pytest_databases.docker.postgres",
]


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def anyio_backend_options() -> dict[str, bool]:
    """Prefer uvloop when available for AnyIO's asyncio backend."""
    try:
        import uvloop  # noqa: F401
    except ImportError:
        return {}
    return {"use_uvloop": True}


@pytest.fixture(name="engine", scope="session")
async def fx_engine(postgres_service: PostgresService) -> AsyncGenerator[AsyncEngine, None]:
    """PostgreSQL instance for testing.

    Uses asyncpg driver (native async) instead of psycopg (greenlet-based)
    to avoid MissingGreenlet errors in tests.

    Returns:
        Async SQLAlchemy engine instance.
    """
    # Set DATABASE_URL for the app to use
    db_url = URL(
        drivername="postgresql+asyncpg",
        username=postgres_service.user,
        password=postgres_service.password,
        host=postgres_service.host,
        port=postgres_service.port,
        database=postgres_service.database,
        query={},  # type:ignore[arg-type]
    )
    os.environ["DATABASE_URL"] = str(db_url)

    engine = create_async_engine(
        db_url,
        echo=False,
        poolclass=NullPool,
    )

    yield engine

    await engine.dispose()


@pytest.fixture(name="sessionmaker", scope="session")
def fx_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create sessionmaker factory bound to test engine."""
    return async_sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture(name="db_schema", scope="session")
async def fx_db_schema(engine: AsyncEngine) -> AsyncGenerator[None, None]:
    """Create schema once per test session.

    Note: Schema is created once and not dropped until session ends.
    Individual tests use db_cleanup for per-test isolation.
    """
    metadata = UUIDAuditBase.registry.metadata
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)


@pytest.fixture
async def db_cleanup(engine: AsyncEngine, db_schema: None) -> AsyncGenerator[None, None]:
    """Per-test database cleanup for isolation.

    Truncates all tables before each test to ensure clean state.
    This is faster than drop/create but still provides isolation.
    """
    yield
    # Clean up after test
    metadata = UUIDAuditBase.registry.metadata
    async with engine.begin() as conn:
        for table in reversed(metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture
async def session(
    sessionmaker: async_sessionmaker[AsyncSession],
    db_cleanup: None,
) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests with cleanup.

    Uses sessionmaker pattern which properly handles greenlet context
    for async psycopg driver.
    """
    async with sessionmaker() as session:
        yield session


# -----------------------------------------------------------------------------
# App and client fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def app(engine: AsyncEngine, db_schema: None) -> Litestar:
    """Create Litestar app for testing.

    The app uses the same PostgreSQL database as the test session.
    """
    from app.server.asgi import create_app

    return create_app()


# -----------------------------------------------------------------------------
# Email fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def email_service() -> EmailService:
    """Create EmailService instance for testing with in-memory backend."""
    config = EmailConfig(backend="memory")
    return EmailService(config=config)


@pytest.fixture
def email_outbox() -> list:
    """Get the email outbox and clear it before each test."""
    InMemoryBackend.clear()
    return InMemoryBackend.outbox
