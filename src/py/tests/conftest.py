"""Root pytest configuration, PostgreSQL template fixtures, and test isolation hooks."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

os.environ.update(
    {
        "SECRET_KEY": "test-secret-key-minimum-32-bytes-long-0123456789",
        "DATABASE_ECHO": "false",
        "DATABASE_ECHO_POOL": "false",
        "COOKIE_SECURE": "false",
        "QUEUES_MAX_CONCURRENCY": "2",
        "QUEUES_POLL_INTERVAL": "0.1",
        "QUEUES_PLACEMENT": "external",
        "VITE_PORT": "3006",
        "VITE_DEV_MODE": "false",
        "EMAIL_ENABLED": "true",
        "EMAIL_BACKEND": "memory",
        "LITESTAR_DEBUG": "false",
        "MCP_ENABLED": "true",
    }
)

import pytest
from advanced_alchemy.base import UUIDv7AuditBase
from litestar_autowire import clear_autowire_cache
from litestar_email import EmailConfig, EmailService, InMemoryBackend
from sqlalchemy import URL, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.db import models as m  # noqa: F401

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable, Generator

    from pytest_databases.docker.postgres import PostgresService
    from pytest_databases.types import PostgresXdistIsolationLevel
    from sqlalchemy.ext.asyncio import AsyncEngine

pytest_plugins = [
    "tests.data_fixtures",
    "pytest_databases.docker",
    "pytest_databases.docker.postgres",
]

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Select asyncio backend for AnyIO tests."""
    return "asyncio"


@pytest.fixture(scope="session")
def anyio_backend_options() -> dict[str, bool]:
    """Prefer uvloop when available for AnyIO's asyncio backend."""
    try:
        import uvloop  # noqa: F401
    except ImportError:
        return {}
    return {"use_uvloop": True}


@pytest.fixture(autouse=True)
def reset_autowire_cache() -> Generator[None, None, None]:
    """Clear litestar-autowire discovery cache before and after every test."""
    clear_autowire_cache()
    try:
        yield
    finally:
        clear_autowire_cache()


@pytest.fixture(scope="session")
def xdist_postgres_isolation_level() -> PostgresXdistIsolationLevel:
    """Use pytest-databases PostgreSQL template cloning across workers."""
    return "template"


@pytest.fixture(scope="session")
def postgres_template_fingerprint_sources() -> list[Path]:
    """Invalidate the PostgreSQL template database when models or migrations change."""
    db_root = Path(__file__).resolve().parents[1] / "app" / "db"
    return [db_root / "models", db_root / "migrations"]


@pytest.fixture(scope="session")
def postgres_template_setup() -> Callable[[PostgresService], None]:
    """Create all application, security, and queue tables once inside the template database."""

    def _setup_template(service: PostgresService) -> None:
        async def _create_all() -> None:
            template_url = URL.create(
                drivername="postgresql+asyncpg",
                username=service.user,
                password=service.password,
                host=service.host,
                port=service.port,
                database=service.database,
            )
            template_engine = create_async_engine(template_url, echo=False, poolclass=NullPool)
            try:
                async with template_engine.begin() as conn:
                    await conn.run_sync(UUIDv7AuditBase.registry.metadata.create_all)
            finally:
                await template_engine.dispose()

        asyncio.run(_create_all())

    return _setup_template


@pytest.fixture(name="engine", scope="session")
def fx_engine(postgres_service: PostgresService) -> Generator[AsyncEngine, None, None]:
    """Create a session-scoped asyncpg engine bound to the cloned PostgreSQL worker database."""
    db_url = URL.create(
        drivername="postgresql+asyncpg",
        username=postgres_service.user,
        password=postgres_service.password,
        host=postgres_service.host,
        port=postgres_service.port,
        database=postgres_service.database,
    )
    os.environ["DATABASE_URL"] = db_url.render_as_string(hide_password=False)

    engine = create_async_engine(db_url, echo=False, poolclass=NullPool)
    yield engine
    asyncio.run(engine.dispose())


@pytest.fixture(name="sessionmaker", scope="session")
def fx_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create an async sessionmaker factory bound to the worker PostgreSQL engine."""
    return async_sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture(name="db_schema", scope="session")
def fx_db_schema(engine: AsyncEngine) -> Generator[None, None, None]:
    """Ensure schema tables exist in the cloned worker database."""
    _ = engine
    yield


@pytest.fixture
async def db_cleanup(engine: AsyncEngine, db_schema: None) -> AsyncGenerator[None, None]:
    """Truncate all application tables after each test for fast per-test isolation."""
    _ = db_schema
    yield
    table_names = [f'"{table.name}"' for table in UUIDv7AuditBase.registry.metadata.sorted_tables]
    if table_names:
        async with engine.begin() as conn:
            await conn.execute(text(f"TRUNCATE TABLE {', '.join(table_names)} RESTART IDENTITY CASCADE"))


@pytest.fixture
async def session(
    sessionmaker: async_sessionmaker[AsyncSession],
    db_cleanup: None,
) -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated async SQLAlchemy session backed by the worker PostgreSQL database."""
    _ = db_cleanup
    async with sessionmaker() as db_session:
        yield db_session


@pytest.fixture
def email_service() -> EmailService:
    """Create an EmailService instance configured with the in-memory backend."""
    return EmailService(config=EmailConfig(backend="memory"))


@pytest.fixture
def email_outbox() -> Generator[list[Any], None, None]:
    """Clear InMemoryBackend before and after every test and yield its outbox."""
    InMemoryBackend.clear()
    try:
        yield InMemoryBackend.outbox
    finally:
        InMemoryBackend.clear()
