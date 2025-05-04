"""All configuration via environment.

Take note of the environment variable prefixes required for each
settings class, except `AppSettings`.
"""

from __future__ import annotations

import binascii
import json
import os
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, cast

from advanced_alchemy.utils.text import slugify
from litestar.data_extractors import RequestExtractorField
from litestar.serialization import decode_json, encode_json
from litestar.utils.module_loader import module_to_os_path
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from app.__metadata__ import __version__ as current_version
from app.utils.env import get_env

if TYPE_CHECKING:
    from collections.abc import Callable

    from litestar.data_extractors import ResponseExtractorField

DEFAULT_MODULE_NAME = "app"
BASE_DIR: Final[Path] = module_to_os_path(DEFAULT_MODULE_NAME)
STATIC_DIR = Path(BASE_DIR / "server" / "web" / "static")


@dataclass
class DatabaseSettings:
    ECHO: bool = field(default_factory=get_env("DATABASE_ECHO", False))
    """Enable SQLAlchemy engine logs."""
    ECHO_POOL: bool = field(default_factory=get_env("DATABASE_ECHO_POOL", False))
    """Enable SQLAlchemy connection pool logs."""
    POOL_DISABLED: bool = field(default_factory=get_env("DATABASE_POOL_DISABLED", False))
    """Disable SQLAlchemy pool configuration."""
    POOL_MAX_OVERFLOW: int = field(default_factory=get_env("DATABASE_MAX_POOL_OVERFLOW", 10))
    """Max overflow for SQLAlchemy connection pool"""
    POOL_SIZE: int = field(default_factory=get_env("DATABASE_POOL_SIZE", 5))
    """Pool size for SQLAlchemy connection pool"""
    POOL_TIMEOUT: int = field(default_factory=get_env("DATABASE_POOL_TIMEOUT", 30))
    """Time in seconds for timing connections out of the connection pool."""
    POOL_RECYCLE: int = field(default_factory=get_env("DATABASE_POOL_RECYCLE", 300))
    """Amount of time to wait before recycling connections."""
    POOL_PRE_PING: bool = field(default_factory=get_env("DATABASE_PRE_POOL_PING", False))
    """Optionally ping database before fetching a session from the connection pool."""
    URL: str = field(default_factory=get_env("DATABASE_URL", "postgres://app:app@localhost:15432/app"))
    """SQLAlchemy Database URL."""
    MIGRATION_CONFIG: str = field(
        default_factory=get_env("DATABASE_MIGRATION_CONFIG", f"{BASE_DIR}/db/migrations/alembic.ini")
    )
    """The path to the `alembic.ini` configuration file."""
    MIGRATION_PATH: str = field(default_factory=get_env("DATABASE_MIGRATION_PATH", f"{BASE_DIR}/db/migrations"))
    """The path to the `alembic` database migrations."""
    MIGRATION_DDL_VERSION_TABLE: str = field(
        default_factory=get_env("DATABASE_MIGRATION_DDL_VERSION_TABLE", "ddl_version")
    )
    """The name to use for the `alembic` versions table name."""
    FIXTURE_PATH: str = field(default_factory=get_env("DATABASE_FIXTURE_PATH", f"{BASE_DIR}/db/fixtures"))
    """The path to JSON fixture files to load into tables."""
    _engine_instance: AsyncEngine | None = None
    """SQLAlchemy engine instance generated from settings."""

    @property
    def engine(self) -> AsyncEngine:
        return self.get_engine()

    def get_engine(self) -> AsyncEngine:
        if self._engine_instance is not None:
            return self._engine_instance
        url = self.URL.replace("postgresql://", "postgresql+psycopg://")
        if url.startswith("postgresql+asyncpg"):
            engine = create_async_engine(
                url=url,
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
            def _sqla_on_connect(  # pragma: no cover # pyright: ignore[reportUnusedFunction]
                dbapi_connection: Any,
                _: Any,
            ) -> Any:  # pragma: no cover # pyright: ignore[reportUnusedFunction]
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

        elif url.startswith("sqlite+aiosqlite"):
            engine = create_async_engine(
                url=url,
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
            def _sqla_on_connect(  # pragma: no cover # pyright: ignore[reportUnusedFunction]
                dbapi_connection: Any,
                _: Any,
            ) -> Any:
                """Override the default begin statement.  The disables the built in begin execution."""
                dbapi_connection.isolation_level = None

            @event.listens_for(engine.sync_engine, "begin")
            def _sqla_on_begin(  # pragma: no cover # pyright: ignore[reportUnusedFunction]
                dbapi_connection: Any,
            ) -> Any:
                """Emits a custom begin"""
                dbapi_connection.exec_driver_sql("BEGIN")

        else:
            engine = create_async_engine(
                url=url,
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
        self._engine_instance = engine
        return self._engine_instance


@dataclass
class ViteSettings:
    """Server configurations."""

    DEV_MODE: bool = field(default_factory=get_env("VITE_DEV_MODE", False))
    """Start `vite` development server."""
    USE_SERVER_LIFESPAN: bool = field(default_factory=get_env("VITE_USE_SERVER_LIFESPAN", False))
    """Auto start and stop `vite` processes when running in development mode.."""
    HOST: str = field(default_factory=get_env("VITE_HOST", "0.0.0.0"))  # noqa: S104
    """The host the `vite` process will listen on.  Defaults to `0.0.0.0`"""
    PORT: int = field(default_factory=get_env("VITE_PORT", 5173))
    """The port to start vite on.  Default to `5173`"""
    HOT_RELOAD: bool = field(default_factory=get_env("VITE_HOT_RELOAD", False))
    """Start `vite` with HMR enabled."""
    ENABLE_REACT_HELPERS: bool = field(default_factory=get_env("VITE_ENABLE_REACT_HELPERS", False))
    """Enable React support in HMR."""
    BUNDLE_DIR: Path = field(default_factory=get_env("VITE_BUNDLE_DIR", Path(f"{BASE_DIR}/server/web/static")))
    """Bundle directory"""
    RESOURCE_DIR: Path = field(default_factory=get_env("VITE_RESOURCE_DIR", Path("src/js/src")))
    """Resource directory"""
    TEMPLATE_DIR: Path = field(default_factory=get_env("VITE_TEMPLATE_DIR", Path(f"{BASE_DIR}/server/web/templates")))
    """Template directory."""
    ASSET_URL: str = field(default_factory=get_env("ASSET_URL", "/"))
    """Base URL for assets"""

    @property
    def set_static_files(self) -> bool:
        """Serve static assets."""
        return self.ASSET_URL.startswith("/")


@dataclass
class ServerSettings:
    """Server configurations."""

    APP_LOC: str = "dma.asgi:create_app"
    """Path to app executable or factory."""
    HOST: str = field(default_factory=get_env("LITESTAR_HOST", "0.0.0.0"))  # noqa: S104
    """Server network host."""
    PORT: int = field(default_factory=get_env("LITESTAR_PORT", 8000))
    """Server port."""
    KEEPALIVE: int = field(default_factory=get_env("LITESTAR_KEEPALIVE", 65))
    """Seconds to hold connections open (65 is > AWS lb idle timeout)."""
    RELOAD: bool = field(default_factory=get_env("LITESTAR_RELOAD", False))
    """Turn on hot reloading."""
    RELOAD_DIRS: list[str] = field(default_factory=get_env("LITESTAR_RELOAD_DIRS", [f"{BASE_DIR}"]))
    """Directories to watch for reloading."""


@dataclass
class SaqSettings:
    """Server configurations."""

    PROCESSES: int = field(default_factory=get_env("SAQ_PROCESSES", 1))
    """The number of worker processes to start.

    Default is set to 1.
    """
    CONCURRENCY: int = field(default_factory=get_env("SAQ_CONCURRENCY", 10))
    """The number of concurrent jobs allowed to execute per worker process.

    Default is set to 10.
    """
    WEB_ENABLED: bool = field(default_factory=get_env("SAQ_WEB_ENABLED", True))
    """If true, the worker admin UI is hosted on worker startup."""
    USE_SERVER_LIFESPAN: bool = field(default_factory=get_env("SAQ_USE_SERVER_LIFESPAN", True))
    """Auto start and stop `saq` processes when starting the Litestar application."""


@dataclass
class StorageSettings:
    """Storage configurations."""

    PUBLIC_STORAGE_KEY: str = field(default_factory=get_env("PUBLIC_STORAGE_KEY", "public"))
    """The key to the public storage directory."""
    PUBLIC_STORAGE_URI: str = field(default_factory=get_env("PUBLIC_STORAGE_PATH_URI", f"{BASE_DIR}/storage/public"))
    """The path to the public storage directory."""
    PUBLIC_STORAGE_OPTIONS: dict[str, Any] = field(default_factory=get_env("PUBLIC_STORAGE_OPTIONS", {}))
    """The options to use for the public storage directory."""
    PRIVATE_STORAGE_KEY: str = field(default_factory=get_env("PRIVATE_STORAGE_KEY", "private"))
    """The key to the private storage directory."""
    PRIVATE_STORAGE_URI: str = field(default_factory=get_env("PRIVATE_STORAGE_PATH_URI", f"{BASE_DIR}/storage/private"))
    """The path to the private storage directory."""
    PRIVATE_STORAGE_OPTIONS: dict[str, Any] = field(default_factory=get_env("PRIVATE_STORAGE_OPTIONS", {}))
    """The options to use for the private storage directory."""


@dataclass
class AppSettings:
    """Application configuration"""

    NAME: str = field(default_factory=lambda: "Litestar Fullstack Template")
    """Application name."""
    VERSION: str = field(default=f"v{current_version}")
    """Current application"""
    CONTACT_NAME: str = field(default="Admin")
    """Application contact name"""
    CONTACT_EMAIL: str = field(default="admin@localhost")
    """Application contact email"""
    URL: str = field(default_factory=get_env("APP_URL", "http://localhost:8000"))
    """The frontend base URL"""
    DEBUG: bool = field(default_factory=get_env("LITESTAR_DEBUG", False))
    """Run `Litestar` with `debug=True`."""
    SECRET_KEY: str = field(
        default_factory=get_env("SECRET_KEY", binascii.hexlify(os.urandom(32)).decode(encoding="utf-8")),
    )
    """Application secret key."""
    JWT_ENCRYPTION_ALGORITHM: str = "HS256"
    """JWT Algorithm to use"""
    ALLOWED_CORS_ORIGINS: list[str] | str = field(default_factory=get_env("ALLOWED_CORS_ORIGINS", ["*"], list[str]))
    """Allowed CORS Origins"""
    CSRF_COOKIE_NAME: str = field(default_factory=get_env("CSRF_COOKIE_NAME", "XSRF-TOKEN"))
    """CSRF Cookie Name"""
    CSRF_HEADER_NAME: str = field(default_factory=get_env("CSRF_HEADER_NAME", "X-XSRF-TOKEN"))
    """CSRF Header Name"""
    CSRF_COOKIE_SECURE: bool = field(default_factory=get_env("CSRF_COOKIE_SECURE", False))
    """CSRF Secure Cookie"""
    STATIC_DIR: Path = field(default_factory=get_env("STATIC_DIR", STATIC_DIR))
    """Default URL where static assets are located."""
    STATIC_URL: str = field(default_factory=get_env("STATIC_URL", "/web/"))
    """URL Location for Static assets."""
    BASE_URL: str | None = None
    """Fully qualified path to optional use for URL generation."""
    DEV_MODE: bool = field(default_factory=get_env("VITE_DEV_MODE", False))
    """Toggle dev mode flag.  This can be used enable extra processes during development."""
    ENABLE_INSTRUMENTATION: bool = False
    """Enable OpenTelemetry instrumentation"""
    GOOGLE_OAUTH2_CLIENT_ID: str = field(default_factory=get_env("GOOGLE_OAUTH2_CLIENT_ID", ""))
    """Google Client ID"""
    GOOGLE_OAUTH2_CLIENT_SECRET: str = field(default_factory=get_env("GOOGLE_OAUTH2_CLIENT_SECRET", ""))
    """Google Client Secret"""
    ENV_SECRETS: str = field(default_factory=get_env("ENV_SECRETS", "runtime-secrets"))
    """Path to environment secrets."""

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
                    self.ALLOWED_CORS_ORIGINS = json.loads(self.ALLOWED_CORS_ORIGINS)  # pyright: ignore[reportConstantRedefinition]
                except (SyntaxError, ValueError):
                    # Handle potential errors if the string is not a valid Python literal.
                    msg = "ALLOWED_CORS_ORIGINS is not a valid list representation."
                    raise ValueError(msg) from None
            else:
                # Split the string by commas into a list if it is not meant to be a list representation.
                self.ALLOWED_CORS_ORIGINS = [host.strip() for host in self.ALLOWED_CORS_ORIGINS.split(",")]  # pyright: ignore[reportConstantRedefinition]


@dataclass
class LogSettings:
    """Logger configuration"""

    # https://stackoverflow.com/a/1845097/6560549
    EXCLUDE_PATHS: str = r"\A(?!x)x"
    """Regex to exclude paths from logging."""
    INCLUDE_COMPRESSED_BODY: bool = False
    """Include 'body' of compressed responses in log output."""
    LEVEL: int = field(default_factory=get_env("LOG_LEVEL", 30))
    """Stdlib log levels.

    Only emit logs at this level, or higher.
    """
    OBFUSCATE_COOKIES: set[str] = field(default_factory=lambda: {"session", "XSRF-TOKEN"})
    """Request cookie keys to obfuscate."""
    OBFUSCATE_HEADERS: set[str] = field(default_factory=lambda: {"Authorization", "X-API-KEY", "X-XSRF-TOKEN"})
    """Request header keys to obfuscate."""
    REQUEST_FIELDS: list[RequestExtractorField] = field(
        default_factory=get_env(
            "LOG_REQUEST_FIELDS",
            [
                "path",
                "method",
                "query",
                "path_params",
            ],
            list[RequestExtractorField],
        ),
    )
    """Attributes of the [Request][litestar.connection.request.Request] to be
    logged."""
    RESPONSE_FIELDS: list[ResponseExtractorField] = field(
        default_factory=cast(
            "Callable[[],list[ResponseExtractorField]]",
            get_env(
                "LOG_RESPONSE_FIELDS",
                ["status_code"],
            ),
        )
    )
    """Attributes of the [Response][litestar.response.Response] to be
    logged."""
    SAQ_LEVEL: int = field(default_factory=get_env("SAQ_LOG_LEVEL", 50))
    """Level to log SAQ logs."""
    SQLALCHEMY_LEVEL: int = field(default_factory=get_env("SQLALCHEMY_LOG_LEVEL", 30))
    """Level to log SQLAlchemy logs."""
    ASGI_ACCESS_LEVEL: int = field(default_factory=get_env("ASGI_ACCESS_LOG_LEVEL", 30))
    """Level to log uvicorn access logs."""
    ASGI_ERROR_LEVEL: int = field(default_factory=get_env("ASGI_ERROR_LOG_LEVEL", 30))
    """Level to log uvicorn error logs."""


@dataclass
class Settings:
    app: AppSettings = field(default_factory=AppSettings)
    db: DatabaseSettings = field(default_factory=DatabaseSettings)
    vite: ViteSettings = field(default_factory=ViteSettings)
    server: ServerSettings = field(default_factory=ServerSettings)
    saq: SaqSettings = field(default_factory=SaqSettings)
    log: LogSettings = field(default_factory=LogSettings)
    storage: StorageSettings = field(default_factory=StorageSettings)

    @classmethod
    @lru_cache(maxsize=1, typed=True)
    def from_env(cls, dotenv_filename: str = ".env") -> Settings:
        import structlog
        from dotenv import load_dotenv
        from litestar.cli._utils import console  # pyright: ignore[reportPrivateImportUsage]

        logger = structlog.get_logger()
        _secret_id = os.environ.get("ENV_SECRETS", None)  # use this to load secrets in a container
        env_file = Path(f"{os.curdir}/{dotenv_filename}")
        env_file_exists = env_file.is_file()
        if env_file_exists:
            console.print(f"[yellow]Loading environment configuration from {dotenv_filename}[/]")
            load_dotenv(env_file, override=True)
        try:
            db: DatabaseSettings = DatabaseSettings()
            server: ServerSettings = ServerSettings()
            saq: SaqSettings = SaqSettings()
            vite: ViteSettings = ViteSettings()
            app: AppSettings = AppSettings()
            log: LogSettings = LogSettings()
            storage: StorageSettings = StorageSettings()
        except Exception as e:  # noqa: BLE001
            logger.fatal("Could not load settings. %s", e)
            sys.exit(1)
        return Settings(app=app, db=db, vite=vite, server=server, saq=saq, log=log, storage=storage)


def get_settings(dotenv_filename: str = ".env") -> Settings:
    return Settings.from_env(dotenv_filename)
