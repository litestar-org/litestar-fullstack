from __future__ import annotations

import binascii
import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

from advanced_alchemy.utils.text import slugify
from litestar.serialization import decode_json, encode_json
from litestar.utils.module_loader import module_to_os_path
from redis.asyncio import Redis
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

if TYPE_CHECKING:
    from litestar.data_extractors import RequestExtractorField, ResponseExtractorField

DEFAULT_MODULE_NAME = "app"
BASE_DIR: Final[Path] = module_to_os_path(DEFAULT_MODULE_NAME)

TRUE_VALUES = {"True", "true", "1", "yes", "Y", "T"}


@dataclass
class DatabaseSettings:
    ECHO: bool = field(
        default_factory=lambda: os.getenv("DATABASE_ECHO", "False") in TRUE_VALUES,
    )
    """Enable SQLAlchemy engine logs."""
    ECHO_POOL: bool = field(
        default_factory=lambda: os.getenv("DATABASE_ECHO_POOL", "False") in TRUE_VALUES,
    )
    """Enable SQLAlchemy connection pool logs."""
    POOL_DISABLED: bool = field(
        default_factory=lambda: os.getenv("DATABASE_POOL_DISABLED", "False") in TRUE_VALUES,
    )
    """Disable SQLAlchemy pool configuration."""
    POOL_MAX_OVERFLOW: int = field(default_factory=lambda: int(os.getenv("DATABASE_MAX_POOL_OVERFLOW", "10")))
    """Max overflow for SQLAlchemy connection pool"""
    POOL_SIZE: int = field(default_factory=lambda: int(os.getenv("DATABASE_POOL_SIZE", "5")))
    """Pool size for SQLAlchemy connection pool"""
    POOL_TIMEOUT: int = field(default_factory=lambda: int(os.getenv("DATABASE_POOL_TIMEOUT", "30")))
    """Time in seconds for timing connections out of the connection pool."""
    POOL_RECYCLE: int = field(default_factory=lambda: int(os.getenv("DATABASE_POOL_RECYCLE", "300")))
    """Amount of time to wait before recycling connections."""
    POOL_PRE_PING: bool = field(
        default_factory=lambda: os.getenv("DATABASE_PRE_POOL_PING", "False") in TRUE_VALUES,
    )
    """Optionally ping database before fetching a session from the connection pool."""
    URL: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite+aiosqlite:///db.sqlite3"))
    """SQLAlchemy Database URL."""
    MIGRATION_CONFIG: str = f"{BASE_DIR}/db/migrations/alembic.ini"
    """The path to the `alembic.ini` configuration file."""
    MIGRATION_PATH: str = f"{BASE_DIR}/db/migrations"
    """The path to the `alembic` database migrations."""
    MIGRATION_DDL_VERSION_TABLE: str = "ddl_version"
    """The name to use for the `alembic` versions table name."""
    FIXTURE_PATH: str = f"{BASE_DIR}/db/fixtures"
    """The path to JSON fixture files to load into tables."""
    _engine_instance: AsyncEngine | None = None
    """SQLAlchemy engine instance generated from settings."""

    @property
    def engine(self) -> AsyncEngine:
        return self.get_engine()

    def get_engine(self) -> AsyncEngine:
        if self._engine_instance is not None:
            return self._engine_instance
        if self.URL.startswith("postgresql+asyncpg"):
            engine = create_async_engine(
                url=self.URL,
                future=True,
                json_serializer=encode_json,
                json_deserializer=decode_json,
                echo=self.ECHO,
                echo_pool=self.ECHO_POOL,
                max_overflow=self.POOL_MAX_OVERFLOW,
                pool_size=self.POOL_SIZE,
                pool_timeout=self.POOL_TIMEOUT,
                pool_recycle=self.POOL_RECYCLE,
                pool_pre_ping=self.POOL_PRE_PING,
                pool_use_lifo=True,  # use lifo to reduce the number of idle connections
                poolclass=NullPool if self.POOL_DISABLED else None,
            )
            """Database session factory.

            See [`async_sessionmaker()`][sqlalchemy.ext.asyncio.async_sessionmaker].
            """

            @event.listens_for(engine.sync_engine, "connect")
            def _sqla_on_connect(dbapi_connection: Any, _: Any) -> Any:  # pragma: no cover
                """Using msgspec for serialization of the json column values means that the
                output is binary, not `str` like `json.dumps` would output.
                SQLAlchemy expects that the json serializer returns `str` and calls `.encode()` on the value to
                turn it to bytes before writing to the JSONB column. I'd need to either wrap `serialization.to_json` to
                return a `str` so that SQLAlchemy could then convert it to binary, or do the following, which
                changes the behaviour of the dialect to expect a binary value from the serializer.
                See Also https://github.com/sqlalchemy/sqlalchemy/blob/14bfbadfdf9260a1c40f63b31641b27fe9de12a0/lib/sqlalchemy/dialects/postgresql/asyncpg.py#L934  pylint: disable=line-too-long
                """

                def encoder(bin_value: bytes) -> bytes:
                    return b"\x01" + encode_json(bin_value)

                def decoder(bin_value: bytes) -> Any:
                    # the byte is the \x01 prefix for jsonb used by PostgreSQL.
                    # asyncpg returns it when format='binary'
                    return decode_json(bin_value[1:])

                dbapi_connection.await_(
                    dbapi_connection.driver_connection.set_type_codec(
                        "jsonb",
                        encoder=encoder,
                        decoder=decoder,
                        schema="pg_catalog",
                        format="binary",
                    ),
                )
                dbapi_connection.await_(
                    dbapi_connection.driver_connection.set_type_codec(
                        "json",
                        encoder=encoder,
                        decoder=decoder,
                        schema="pg_catalog",
                        format="binary",
                    ),
                )
        elif self.URL.startswith("sqlite+aiosqlite"):
            engine = create_async_engine(
                url=self.URL,
                future=True,
                json_serializer=encode_json,
                json_deserializer=decode_json,
                echo=self.ECHO,
                echo_pool=self.ECHO_POOL,
                pool_recycle=self.POOL_RECYCLE,
                pool_pre_ping=self.POOL_PRE_PING,
            )
            """Database session factory.

            See [`async_sessionmaker()`][sqlalchemy.ext.asyncio.async_sessionmaker].
            """

            @event.listens_for(engine.sync_engine, "connect")
            def _sqla_on_connect(dbapi_connection: Any, _: Any) -> Any:  # pragma: no cover
                """Override the default begin statement.  The disables the built in begin execution."""
                dbapi_connection.isolation_level = None

            @event.listens_for(engine.sync_engine, "begin")
            def _sqla_on_begin(dbapi_connection: Any) -> Any:  # pragma: no cover
                """Emits a custom begin"""
                dbapi_connection.exec_driver_sql("BEGIN")
        else:
            engine = create_async_engine(
                url=self.URL,
                future=True,
                json_serializer=encode_json,
                json_deserializer=decode_json,
                echo=self.ECHO,
                echo_pool=self.ECHO_POOL,
                max_overflow=self.POOL_MAX_OVERFLOW,
                pool_size=self.POOL_SIZE,
                pool_timeout=self.POOL_TIMEOUT,
                pool_recycle=self.POOL_RECYCLE,
                pool_pre_ping=self.POOL_PRE_PING,
            )
        self._engine_instance = engine
        return self._engine_instance


@dataclass
class ViteSettings:
    """Server configurations."""

    DEV_MODE: bool = field(
        default_factory=lambda: os.getenv("VITE_DEV_MODE", "False") in TRUE_VALUES,
    )
    """Start `vite` development server."""
    USE_SERVER_LIFESPAN: bool = field(
        default_factory=lambda: os.getenv("VITE_USE_SERVER_LIFESPAN", "True") in TRUE_VALUES,
    )
    """Auto start and stop `vite` processes when running in development mode.."""
    HOST: str = field(default_factory=lambda: os.getenv("VITE_HOST", "0.0.0.0"))  # noqa: S104
    """The host the `vite` process will listen on.  Defaults to `0.0.0.0`"""
    PORT: int = field(default_factory=lambda: int(os.getenv("VITE_PORT", "5173")))
    """The port to start vite on.  Default to `5173`"""
    HOT_RELOAD: bool = field(
        default_factory=lambda: os.getenv("VITE_HOT_RELOAD", "True") in TRUE_VALUES,
    )
    """Start `vite` with HMR enabled."""
    ENABLE_REACT_HELPERS: bool = field(
        default_factory=lambda: os.getenv("VITE_ENABLE_REACT_HELPERS", "True") in TRUE_VALUES,
    )
    """Enable React support in HMR."""
    BUNDLE_DIR: Path = field(default_factory=lambda: Path(f"{BASE_DIR}/domain/web/public"))
    """Bundle directory"""
    RESOURCE_DIR: Path = field(default_factory=lambda: Path("resources"))
    """Resource directory"""
    TEMPLATE_DIR: Path = field(default_factory=lambda: Path(f"{BASE_DIR}/domain/web/templates"))
    """Template directory."""
    ASSET_URL: str = field(default_factory=lambda: os.getenv("ASSET_URL", "/static/"))
    """Base URL for assets"""

    @property
    def set_static_files(self) -> bool:
        """Serve static assets."""
        return self.ASSET_URL.startswith("/")


@dataclass
class ServerSettings:
    """Server configurations."""

    APP_LOC: str = "app.asgi:app"
    """Path to app executable, or factory."""
    APP_LOC_IS_FACTORY: bool = False
    """Indicate if APP_LOC points to an executable or factory."""
    HOST: str = field(default_factory=lambda: os.getenv("LITESTAR_HOST", "0.0.0.0"))  # noqa: S104
    """Server network host."""
    PORT: int = field(default_factory=lambda: int(os.getenv("LITESTAR_PORT", "8000")))
    """Server port."""
    KEEPALIVE: int = field(default_factory=lambda: int(os.getenv("LITESTAR_KEEPALIVE", "65")))
    """Seconds to hold connections open (65 is > AWS lb idle timeout)."""
    RELOAD: bool = field(
        default_factory=lambda: os.getenv("LITESTAR_RELOAD", "False") in TRUE_VALUES,
    )
    """Turn on hot reloading."""
    RELOAD_DIRS: list[str] = field(default_factory=lambda: [f"{BASE_DIR}"])
    """Directories to watch for reloading."""
    HTTP_WORKERS: int | None = field(
        default_factory=lambda: int(os.getenv("WEB_CONCURRENCY")) if os.getenv("WEB_CONCURRENCY") is not None else None,  # type: ignore[arg-type]
    )
    """Number of HTTP Worker processes to be spawned by Uvicorn."""


@dataclass
class SaqSettings:
    """Server configurations."""

    PROCESSES: int = field(default_factory=lambda: int(os.getenv("SAQ_PROCESSES", "1")))
    """The number of worker processes to start.

    Default is set to 1.
    """
    CONCURRENCY: int = field(default_factory=lambda: int(os.getenv("SAQ_CONCURRENCY", "10")))
    """The number of concurrent jobs allowed to execute per worker process.

    Default is set to 10.
    """
    WEB_ENABLED: bool = field(
        default_factory=lambda: os.getenv("SAQ_WEB_ENABLED", "True") in TRUE_VALUES,
    )
    """If true, the worker admin UI is hosted on worker startup."""
    USE_SERVER_LIFESPAN: bool = field(
        default_factory=lambda: os.getenv("SAQ_USE_SERVER_LIFESPAN", "True") in TRUE_VALUES,
    )
    """Auto start and stop `saq` processes when starting the Litestar application."""


@dataclass
class LogSettings:
    """Logger configuration"""

    # https://stackoverflow.com/a/1845097/6560549
    EXCLUDE_PATHS: str = r"\A(?!x)x"
    """Regex to exclude paths from logging."""
    HTTP_EVENT: str = "HTTP"
    """Log event name for logs from Litestar handlers."""
    INCLUDE_COMPRESSED_BODY: bool = False
    """Include 'body' of compressed responses in log output."""
    LEVEL: int = field(default_factory=lambda: int(os.getenv("LOG_LEVEL", "10")))
    """Stdlib log levels.

    Only emit logs at this level, or higher.
    """
    OBFUSCATE_COOKIES: set[str] = field(default_factory=lambda: {"session"})
    """Request cookie keys to obfuscate."""
    OBFUSCATE_HEADERS: set[str] = field(default_factory=lambda: {"Authorization", "X-API-KEY", "X-XSRF-TOKEN"})
    """Request header keys to obfuscate."""
    JOB_FIELDS: list[str] = field(
        default_factory=lambda: [
            "function",
            "kwargs",
            "key",
            "scheduled",
            "attempts",
            "completed",
            "queued",
            "started",
            "result",
            "error",
        ],
    )
    """Attributes of the SAQ.

    [`Job`](https://github.com/tobymao/saq/blob/master/saq/job.py) to be
    logged.
    """
    REQUEST_FIELDS: list[RequestExtractorField] = field(
        default_factory=lambda: [
            "path",
            "method",
            "headers",
            "cookies",
            "query",
            "path_params",
            "body",
        ],
    )
    """Attributes of the [Request][litestar.connection.request.Request] to be
    logged."""
    RESPONSE_FIELDS: list[ResponseExtractorField] = field(
        default_factory=lambda: [
            "status_code",
            "cookies",
            "headers",
            "body",
        ],
    )
    """Attributes of the [Response][litestar.response.Response] to be
    logged."""
    WORKER_EVENT: str = "Worker"
    """Log event name for logs from SAQ worker."""
    SAQ_LEVEL: int = 20
    """Level to log SAQ logs."""
    SQLALCHEMY_LEVEL: int = 20
    """Level to log SQLAlchemy logs."""
    UVICORN_ACCESS_LEVEL: int = 20
    """Level to log uvicorn access logs."""
    UVICORN_ERROR_LEVEL: int = 20
    """Level to log uvicorn error logs."""
    GRANIAN_ACCESS_LEVEL: int = 30
    """Level to log uvicorn access logs."""
    GRANIAN_ERROR_LEVEL: int = 20
    """Level to log uvicorn error logs."""


@dataclass
class RedisSettings:
    URL: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    """A Redis connection URL."""
    SOCKET_CONNECT_TIMEOUT: int = field(default_factory=lambda: int(os.getenv("REDIS_CONNECT_TIMEOUT", "5")))
    """Length of time to wait (in seconds) for a connection to become
    active."""
    HEALTH_CHECK_INTERVAL: int = field(default_factory=lambda: int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "5")))
    """Length of time to wait (in seconds) before testing connection health."""
    SOCKET_KEEPALIVE: bool = field(
        default_factory=lambda: os.getenv("REDIS_SOCKET_KEEPALIVE", "True") in TRUE_VALUES,
    )
    """Length of time to wait (in seconds) between keepalive commands."""
    _redis_instance: Redis | None = None
    """Redis instance generated from settings."""

    @property
    def client(self) -> Redis:
        return self.get_client()

    def get_client(self) -> Redis:
        if self._redis_instance is not None:
            return self._redis_instance
        self._redis_instance = Redis.from_url(
            url=self.URL,
            encoding="utf-8",
            decode_responses=False,
            socket_connect_timeout=self.SOCKET_CONNECT_TIMEOUT,
            socket_keepalive=self.SOCKET_KEEPALIVE,
            health_check_interval=self.HEALTH_CHECK_INTERVAL,
        )
        return self._redis_instance


@dataclass
class AppSettings:
    """Application configuration"""

    URL: str = field(default_factory=lambda: os.getenv("APP_URL", "http://localhost:8000"))
    """The frontend base URL"""
    DEBUG: bool = field(default_factory=lambda: os.getenv("LITESTAR_DEBUG", "False") in TRUE_VALUES)
    """Run `Litestar` with `debug=True`."""
    SECRET_KEY: str = field(
        default_factory=lambda: os.getenv("SECRET_KEY", binascii.hexlify(os.urandom(32)).decode(encoding="utf-8")),
    )
    """Application secret key."""
    NAME: str = field(default_factory=lambda: "app")
    """Application name."""
    ALLOWED_CORS_ORIGINS: list[str] | str = field(default_factory=lambda: os.getenv("ALLOWED_CORS_ORIGINS", '["*"]'))
    """Allowed CORS Origins"""
    CSRF_COOKIE_NAME: str = field(default_factory=lambda: "XSRF-TOKEN")
    """CSRF Cookie Name"""
    CSRF_HEADER_NAME: str = field(default_factory=lambda: "X-XSRF-TOKEN")
    """CSRF Header Name"""
    CSRF_COOKIE_SECURE: bool = field(default_factory=lambda: False)
    """CSRF Secure Cookie"""
    OPENTELEMETRY_ENABLED: bool = field(
        default_factory=lambda: os.getenv("OPENTELEMETRY_ENABLED", "False") in TRUE_VALUES,
    )
    """Enable Opentelemetry configuration."""

    @property
    def slug(self) -> str:
        """Return a slugified name.

        Returns:
            `self.NAME`, all lowercase and hyphens instead of spaces.
        """
        return slugify(self.NAME)

    def __post_init__(self) -> None:
        # Check if the ALLOWED_CORS_ORIGINS is a string.
        if isinstance(self.ALLOWED_CORS_ORIGINS, str):
            # Check if the string starts with "[" and ends with "]", indicating a list.
            if self.ALLOWED_CORS_ORIGINS.startswith("[") and self.ALLOWED_CORS_ORIGINS.endswith("]"):
                try:
                    # Safely evaluate the string as a Python list.
                    self.ALLOWED_CORS_ORIGINS = json.loads(self.ALLOWED_CORS_ORIGINS)
                except (SyntaxError, ValueError):
                    # Handle potential errors if the string is not a valid Python literal.
                    msg = "ALLOWED_CORS_ORIGINS is not a valid list representation."
                    raise ValueError(msg) from None
            else:
                # Split the string by commas into a list if it is not meant to be a list representation.
                self.ALLOWED_CORS_ORIGINS = [host.strip() for host in self.ALLOWED_CORS_ORIGINS.split(",")]


@dataclass
class Settings:
    app: AppSettings = field(default_factory=AppSettings)
    db: DatabaseSettings = field(default_factory=DatabaseSettings)
    vite: ViteSettings = field(default_factory=ViteSettings)
    server: ServerSettings = field(default_factory=ServerSettings)
    log: LogSettings = field(default_factory=LogSettings)
    redis: RedisSettings = field(default_factory=RedisSettings)
    saq: SaqSettings = field(default_factory=SaqSettings)

    @classmethod
    def from_env(cls, dotenv_filename: str = ".env") -> Settings:
        from litestar.cli._utils import console

        env_file = Path(f"{os.curdir}/{dotenv_filename}")
        if env_file.is_file():
            from dotenv import load_dotenv

            console.print(f"[yellow]Loading environment configuration from {dotenv_filename}[/]")

            load_dotenv(env_file, override=True)
        return Settings()


@lru_cache(maxsize=1, typed=True)
def get_settings() -> Settings:
    return Settings.from_env()
