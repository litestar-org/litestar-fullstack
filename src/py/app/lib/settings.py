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
from typing import TYPE_CHECKING, Final, cast

from advanced_alchemy.utils.text import slugify
from litestar.data_extractors import RequestExtractorField
from litestar.utils.module_loader import module_to_os_path

from app.__metadata__ import __version__ as current_version
from app.utils.env import get_env

if TYPE_CHECKING:
    from collections.abc import Callable

    from litestar.config.compression import CompressionConfig
    from litestar.config.cors import CORSConfig
    from litestar.config.csrf import CSRFConfig
    from litestar.data_extractors import ResponseExtractorField
    from litestar.plugins.problem_details import ProblemDetailsConfig
    from litestar.plugins.sqlalchemy import SQLAlchemyAsyncConfig
    from litestar.plugins.structlog import StructlogConfig
    from litestar_saq import SAQConfig
    from litestar_vite import ViteConfig
    from sqlalchemy.ext.asyncio import AsyncEngine

DEFAULT_MODULE_NAME = "app"
BASE_DIR: Final[Path] = module_to_os_path(DEFAULT_MODULE_NAME)
STATIC_DIR = Path(BASE_DIR / "server" / "public")
TEMPLATE_DIR = Path(BASE_DIR / "server" / "templates")


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
        from app.utils.engine_factory import create_sqlalchemy_engine

        self._engine_instance = create_sqlalchemy_engine(self)
        return self._engine_instance

    def get_config(self) -> SQLAlchemyAsyncConfig:
        from litestar.plugins.sqlalchemy import AlembicAsyncConfig, AsyncSessionConfig, SQLAlchemyAsyncConfig

        return SQLAlchemyAsyncConfig(
            engine_instance=self.get_engine(),
            before_send_handler="autocommit",
            session_config=AsyncSessionConfig(expire_on_commit=False),
            alembic_config=AlembicAsyncConfig(
                version_table_name=self.MIGRATION_DDL_VERSION_TABLE,
                script_config=self.MIGRATION_CONFIG,
                script_location=self.MIGRATION_PATH,
            ),
        )


@dataclass
class ViteSettings:
    """Vite build tool configurations."""

    DEV_MODE: bool = field(default_factory=get_env("VITE_DEV_MODE", False))
    """Start `vite` development server."""
    BUNDLE_DIR: Path = field(default_factory=get_env("VITE_BUNDLE_DIR", STATIC_DIR))
    """Bundle directory for built assets."""
    ASSET_URL: str = field(default_factory=get_env("ASSET_URL", "/"))
    """Base URL for assets."""

    def get_config(self, base_dir: Path = BASE_DIR.parent.parent) -> ViteConfig:
        from litestar_vite import PathConfig, RuntimeConfig, TypeGenConfig, ViteConfig

        return ViteConfig(
            mode="spa",
            dev_mode=self.DEV_MODE,
            runtime=RuntimeConfig(executor="bun"),
            paths=PathConfig(
                root=base_dir / "js" / "web",
                bundle_dir=self.BUNDLE_DIR,
                asset_url=self.ASSET_URL,
            ),
            types=TypeGenConfig(
                output=base_dir / "js" / "web" / "src" / "lib" / "generated",
                openapi_path=base_dir / "js" / "web" / "src" / "lib" / "generated" / "openapi.json",
                routes_path=base_dir / "js" / "web" / "src" / "lib" / "generated" / "routes.json",
                routes_ts_path=base_dir / "js" / "web" / "src" / "lib" / "generated" / "routes.ts",
                page_props_path=base_dir / "js" / "web" / "src" / "lib" / "generated" / "inertia-pages.json",
                generate_zod=True,
                generate_sdk=True,
                generate_routes=True,
                generate_page_props=True,
                global_route=False,
            ),
        )


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

    def get_config(self, db: DatabaseSettings) -> SAQConfig:
        from litestar_saq import QueueConfig, SAQConfig

        from app.lib.worker import after_process, before_process, on_shutdown, on_startup

        return SAQConfig(
            web_enabled=self.WEB_ENABLED,
            worker_processes=self.PROCESSES,
            use_server_lifespan=self.USE_SERVER_LIFESPAN,
            queue_configs=[
                QueueConfig(
                    name="background-tasks",
                    dsn=db.URL.replace("postgresql+psycopg", "postgresql"),
                    broker_options={
                        "stats_table": "task_queue_stats",
                        "jobs_table": "task_queue",
                        "versions_table": "task_queue_ddl_version",
                    },
                    tasks=[],
                    scheduled_tasks=[],
                    concurrency=20,
                    startup=on_startup,
                    shutdown=on_shutdown,
                    before_process=before_process,
                    after_process=after_process,
                )
            ],
        )


@dataclass
class EmailSettings:
    """Email configuration"""

    ENABLED: bool = field(default_factory=get_env("EMAIL_ENABLED", False))
    """Whether email sending is enabled."""
    BACKEND: str = field(default_factory=get_env("EMAIL_BACKEND", "console"))
    """Email backend to use: smtp, console, locmem."""
    SMTP_HOST: str = field(default_factory=get_env("EMAIL_SMTP_HOST", "localhost"))
    """SMTP server hostname."""
    SMTP_PORT: int = field(default_factory=get_env("EMAIL_SMTP_PORT", 587, int))
    """SMTP server port."""
    SMTP_USER: str = field(default_factory=get_env("EMAIL_SMTP_USER", ""))
    """SMTP username."""
    SMTP_PASSWORD: str = field(default_factory=get_env("EMAIL_SMTP_PASSWORD", ""))
    """SMTP password."""
    USE_TLS: bool = field(default_factory=get_env("EMAIL_USE_TLS", True))
    """Use TLS for SMTP connection."""
    USE_SSL: bool = field(default_factory=get_env("EMAIL_USE_SSL", False))
    """Use SSL for SMTP connection."""
    FROM_EMAIL: str = field(default_factory=get_env("EMAIL_FROM_ADDRESS", "noreply@localhost"))
    """Default from email address."""
    FROM_NAME: str = field(default_factory=get_env("EMAIL_FROM_NAME", "Litestar App"))
    """Default from name."""
    TIMEOUT: int = field(default_factory=get_env("EMAIL_TIMEOUT", 30, int))
    """SMTP connection timeout in seconds."""


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
    CSRF_COOKIE_HTTPONLY: bool = field(default_factory=get_env("CSRF_COOKIE_HTTPONLY", True))
    """CSRF HttpOnly Cookie - True because litestar-vite injects token into HTML as window.__LITESTAR_CSRF__"""
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
    GITHUB_OAUTH2_CLIENT_ID: str = field(default_factory=get_env("GITHUB_OAUTH2_CLIENT_ID", ""))
    """GitHub Client ID"""
    GITHUB_OAUTH2_CLIENT_SECRET: str = field(default_factory=get_env("GITHUB_OAUTH2_CLIENT_SECRET", ""))
    """GitHub Client Secret"""
    ENV_SECRETS: str = field(default_factory=get_env("ENV_SECRETS", "runtime-secrets"))
    """Path to environment secrets."""

    @property
    def google_oauth_enabled(self) -> bool:
        """Check if Google OAuth is configured."""
        return bool(self.GOOGLE_OAUTH2_CLIENT_ID and self.GOOGLE_OAUTH2_CLIENT_SECRET)

    @property
    def github_oauth_enabled(self) -> bool:
        """Check if GitHub OAuth is configured."""
        return bool(self.GITHUB_OAUTH2_CLIENT_ID and self.GITHUB_OAUTH2_CLIENT_SECRET)

    @property
    def slug(self) -> str:
        """Return a slugified name.

        Returns:
            `self.NAME`, all lowercase and hyphens instead of spaces.
        """
        return slugify(self.NAME)

    def get_compression_config(self) -> CompressionConfig:
        from litestar.config.compression import CompressionConfig

        return CompressionConfig(backend="gzip")

    def get_csrf_config(self) -> CSRFConfig:
        from litestar.config.csrf import CSRFConfig

        return CSRFConfig(
            secret=self.SECRET_KEY,
            cookie_secure=self.CSRF_COOKIE_SECURE,
            cookie_httponly=self.CSRF_COOKIE_HTTPONLY,
            cookie_name=self.CSRF_COOKIE_NAME,
            header_name=self.CSRF_HEADER_NAME,
            # Exclude OAuth callbacks since they're initiated externally
            exclude=["/api/auth/oauth/*/callback"],
        )

    def get_cors_config(self) -> CORSConfig:
        from litestar.config.cors import CORSConfig

        return CORSConfig(allow_origins=cast("list[str]", self.ALLOWED_CORS_ORIGINS))

    def get_problem_details_config(self) -> ProblemDetailsConfig:
        from litestar.plugins.problem_details import ProblemDetailsConfig

        return ProblemDetailsConfig(enable_for_all_http_exceptions=True)

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

    def get_structlog_config(self) -> StructlogConfig:
        import logging

        import structlog
        from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
        from litestar.logging.config import LoggingConfig, StructLoggingConfig, default_logger_factory
        from litestar.middleware.logging import LoggingMiddlewareConfig
        from litestar.plugins.structlog import StructlogConfig

        from app.lib import log as log_conf

        return StructlogConfig(
            enable_middleware_logging=False,
            structlog_logging_config=StructLoggingConfig(
                log_exceptions="always",
                processors=log_conf.structlog_processors(as_json=not log_conf.is_tty()),
                logger_factory=default_logger_factory(as_json=not log_conf.is_tty()),
                disable_stack_trace={404, 401, 403, NotAuthorizedException, PermissionDeniedException},
                standard_lib_logging_config=LoggingConfig(
                    log_exceptions="always",
                    disable_stack_trace={404, 401, 403, NotAuthorizedException, PermissionDeniedException},
                    root={"level": logging.getLevelName(self.LEVEL), "handlers": ["queue_listener"]},
                    formatters={
                        "standard": {
                            "()": structlog.stdlib.ProcessorFormatter,
                            "processors": log_conf.stdlib_logger_processors(as_json=not log_conf.is_tty()),
                        },
                    },
                    loggers={
                        "saq": {
                            "propagate": False,
                            "level": self.SAQ_LEVEL,
                            "handlers": ["queue_listener"],
                        },
                        "sqlalchemy.engine": {
                            "propagate": False,
                            "level": self.SQLALCHEMY_LEVEL,
                            "handlers": ["queue_listener"],
                        },
                        "sqlalchemy.pool": {
                            "propagate": False,
                            "level": self.SQLALCHEMY_LEVEL,
                            "handlers": ["queue_listener"],
                        },
                        "opentelemetry.sdk.metrics._internal": {
                            "propagate": False,
                            "level": 40,
                            "handlers": ["queue_listener"],
                        },
                        "httpx": {
                            "propagate": False,
                            "level": max(self.LEVEL, logging.WARNING),
                            "handlers": ["queue_listener"],
                        },
                        "httpcore": {
                            "propagate": False,
                            "level": max(self.LEVEL, logging.WARNING),
                            "handlers": ["queue_listener"],
                        },
                        "_granian": {
                            "propagate": False,
                            "level": self.ASGI_ERROR_LEVEL,
                            "handlers": ["queue_listener"],
                        },
                        "granian.server": {
                            "propagate": False,
                            "level": self.ASGI_ERROR_LEVEL,
                            "handlers": ["queue_listener"],
                        },
                        "granian.access": {
                            "propagate": False,
                            "level": self.ASGI_ACCESS_LEVEL,
                            "handlers": ["queue_listener"],
                        },
                    },
                ),
            ),
            middleware_logging_config=LoggingMiddlewareConfig(
                request_log_fields=self.REQUEST_FIELDS,
                response_log_fields=self.RESPONSE_FIELDS,
            ),
        )


@dataclass
class Settings:
    app: AppSettings = field(default_factory=AppSettings)
    db: DatabaseSettings = field(default_factory=DatabaseSettings)
    vite: ViteSettings = field(default_factory=ViteSettings)
    server: ServerSettings = field(default_factory=ServerSettings)
    saq: SaqSettings = field(default_factory=SaqSettings)
    log: LogSettings = field(default_factory=LogSettings)
    email: EmailSettings = field(default_factory=EmailSettings)

    @classmethod
    @lru_cache(maxsize=1, typed=True)
    def from_env(cls, dotenv_filename: str = ".env") -> Settings:
        import structlog
        from dotenv import load_dotenv
        from litestar.cli._utils import console

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
        except Exception as e:  # noqa: BLE001
            logger.fatal("Could not load settings. %s", e)
            sys.exit(1)
        return Settings(app=app, db=db, vite=vite, server=server, saq=saq, log=log)


def get_settings(dotenv_filename: str = ".env") -> Settings:
    return Settings.from_env(dotenv_filename)


def provide_app_settings() -> AppSettings:
    """Return application settings for dependency injection."""
    return get_settings().app
