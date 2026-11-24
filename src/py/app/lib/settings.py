"""All application configuration loaded from environment variables.

Take note of the environment variable prefixes required for each settings class,
except ``AppSettings``.
"""

from __future__ import annotations

import binascii
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, cast

import structlog
from advanced_alchemy.extensions.litestar import (
    AlembicAsyncConfig,
    AsyncSessionConfig,
    EngineConfig,
    SQLAlchemyAsyncConfig,
)
from advanced_alchemy.utils.text import slugify
from dotenv import load_dotenv
from litestar.cli._utils import console
from litestar.config.compression import CompressionConfig
from litestar.config.cors import CORSConfig
from litestar.data_extractors import RequestExtractorField, ResponseExtractorField
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
from litestar.logging.config import LoggingConfig, StructLoggingConfig, default_logger_factory
from litestar.middleware.logging import LoggingMiddlewareConfig
from litestar.plugins.problem_details import ProblemDetailsConfig
from litestar.plugins.structlog import StructlogConfig
from litestar.serialization import decode_json, encode_json
from litestar.utils.module_loader import module_to_os_path
from litestar_email import EmailConfig, ResendConfig, SMTPConfig
from litestar_mcp import MCPConfig
from litestar_queues import (
    EventDeliveryConfig,
    EventHistoryConfig,
    EventStreamConfig,
    QueueConfig,
    QueueEventsConfig,
    QueueMaintenanceConfig,
    WorkerConfig,
)
from litestar_queues.backends.advanced_alchemy import SQLAlchemyBackendConfig
from litestar_queues.observability import ObservabilityConfig
from litestar_security import SecurityConfig, SecurityHeadersConfig
from litestar_vite import PathConfig, RuntimeConfig, TypeGenConfig, ViteConfig
from sqlalchemy.pool import NullPool

from app.__metadata__ import __version__ as current_version
from app.lib.secrets import derive_subkey
from app.utils.env import TRUE_VALUES, get_config_val, get_env

if TYPE_CHECKING:
    from collections.abc import Callable

    from litestar_queues import ExecutionBackendConfig, WorkerPlacement

DEFAULT_MODULE_NAME: Final[str] = "app"
BASE_DIR: Final[Path] = module_to_os_path(DEFAULT_MODULE_NAME)
STATIC_DIR: Final[Path] = Path(BASE_DIR / "server" / "static" / "web")


def _encode_json_str(value: Any) -> str:
    return encode_json(value).decode("utf-8")


def _get_float_env(key: str, default: float) -> Callable[[], float]:
    def _factory() -> float:
        raw = os.getenv(key)
        return float(raw) if raw else default

    return _factory


def _get_optional_int_env(key: str) -> Callable[[], int | None]:
    def _factory() -> int | None:
        raw = os.getenv(key)
        return int(raw) if raw else None

    return _factory


def _get_optional_bool_env(key: str) -> Callable[[], bool | None]:
    def _factory() -> bool | None:
        raw = os.getenv(key)
        return raw in TRUE_VALUES if raw is not None and raw != "" else None

    return _factory


def _get_list_env(key: str, default: list[str]) -> Callable[[], list[str]]:
    def _factory() -> list[str]:
        raw = os.getenv(key)
        if raw is None:
            return list(default)
        if not raw.strip():
            return []
        parsed = get_config_val(key, list(default), list[str])
        return [item for item in parsed if item]

    return _factory


def _get_optional_list_env(key: str) -> Callable[[], list[str] | None]:
    def _factory() -> list[str] | None:
        raw = os.getenv(key)
        if raw is None or not raw.strip():
            return None
        parsed = get_config_val(key, [], list[str])
        cleaned = [item for item in parsed if item]
        return cleaned or None

    return _factory


def _get_queue_names_env(
    key: str,
    default: tuple[str, ...],
) -> Callable[[], tuple[str, ...]]:
    def _factory() -> tuple[str, ...]:
        if os.getenv(key) is None:
            return default
        parsed = get_config_val(key, list(default), list[str])
        return tuple(item for item in parsed if item)

    return _factory


@dataclass
class DatabaseSettings:
    """SQLAlchemy and Alembic configuration settings."""

    ECHO: bool = field(default_factory=get_env("DATABASE_ECHO", False))
    ECHO_POOL: bool = field(default_factory=get_env("DATABASE_ECHO_POOL", False))
    POOL_DISABLED: bool = field(default_factory=get_env("DATABASE_POOL_DISABLED", False))
    POOL_MAX_OVERFLOW: int = field(default_factory=get_env("DATABASE_MAX_POOL_OVERFLOW", 10))
    POOL_SIZE: int = field(default_factory=get_env("DATABASE_POOL_SIZE", 5))
    POOL_TIMEOUT: int = field(default_factory=get_env("DATABASE_POOL_TIMEOUT", 30))
    POOL_RECYCLE: int = field(default_factory=get_env("DATABASE_POOL_RECYCLE", 300))
    POOL_PRE_PING: bool = field(default_factory=get_env("DATABASE_PRE_POOL_PING", False))
    URL: str = field(default_factory=get_env("DATABASE_URL", "postgresql+asyncpg://app:app@localhost:15432/app"))
    MIGRATION_CONFIG: str = field(
        default_factory=get_env("DATABASE_MIGRATION_CONFIG", f"{BASE_DIR}/db/migrations/alembic.ini")
    )
    MIGRATION_PATH: str = field(default_factory=get_env("DATABASE_MIGRATION_PATH", f"{BASE_DIR}/db/migrations"))
    MIGRATION_DDL_VERSION_TABLE: str = field(
        default_factory=get_env("DATABASE_MIGRATION_DDL_VERSION_TABLE", "ddl_version")
    )
    FIXTURE_PATH: str = field(default_factory=get_env("DATABASE_FIXTURE_PATH", f"{BASE_DIR}/db/fixtures"))

    def normalized_url(self) -> str:
        """Return the database URL normalized to use the ``asyncpg`` driver for PostgreSQL."""
        if self.URL.startswith("postgres://"):
            return self.URL.replace("postgres://", "postgresql+asyncpg://", 1)
        if self.URL.startswith("postgresql://"):
            return self.URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.URL

    def is_postgres(self) -> bool:
        """Return whether the normalized database URL targets PostgreSQL."""
        return self.normalized_url().startswith("postgresql")

    def get_config(self) -> SQLAlchemyAsyncConfig:
        """Build a native Advanced Alchemy async configuration without eager connection startup."""
        url = self.normalized_url()
        use_null_pool = self.POOL_DISABLED or url.startswith("sqlite")
        if use_null_pool:
            engine_config = EngineConfig(
                echo=self.ECHO,
                echo_pool=self.ECHO_POOL,
                poolclass=NullPool,
                json_serializer=_encode_json_str,
                json_deserializer=decode_json,
            )
        else:
            engine_config = EngineConfig(
                echo=self.ECHO,
                echo_pool=self.ECHO_POOL,
                pool_size=self.POOL_SIZE,
                max_overflow=self.POOL_MAX_OVERFLOW,
                pool_timeout=self.POOL_TIMEOUT,
                pool_recycle=self.POOL_RECYCLE,
                pool_pre_ping=self.POOL_PRE_PING,
                pool_use_lifo=True,
                json_serializer=_encode_json_str,
                json_deserializer=decode_json,
            )
        return SQLAlchemyAsyncConfig(
            connection_string=url,
            before_send_handler="autocommit",
            session_config=AsyncSessionConfig(expire_on_commit=False),
            engine_config=engine_config,
            alembic_config=AlembicAsyncConfig(
                version_table_name=self.MIGRATION_DDL_VERSION_TABLE,
                script_config=self.MIGRATION_CONFIG,
                script_location=self.MIGRATION_PATH,
            ),
        )


@dataclass
class QueueSettings:
    """PostgreSQL-backed ``litestar-queues`` configuration settings."""

    PLACEMENT: str = field(default_factory=get_env("QUEUES_PLACEMENT", "server"))
    EXECUTION_BACKEND: str = field(default_factory=get_env("QUEUES_EXECUTION_BACKEND", "local"))
    MAX_CONCURRENCY: int = field(default_factory=get_env("QUEUES_MAX_CONCURRENCY", 8))
    BATCH_SIZE: int = field(default_factory=get_env("QUEUES_BATCH_SIZE", 10))
    POLL_INTERVAL: float = field(default_factory=_get_float_env("QUEUES_POLL_INTERVAL", 0.25))
    QUEUES: tuple[str, ...] = field(
        default_factory=_get_queue_names_env("QUEUES_NAMES", ("default", "emails", "reports", "maintenance"))
    )
    STREAM_ENABLED: bool = field(default_factory=get_env("QUEUES_STREAM_ENABLED", True))
    STREAM_PATH: str = field(default_factory=get_env("QUEUES_STREAM_PATH", "/api/queues/events"))
    TERMINAL_RETENTION_SECONDS: int | None = field(
        default_factory=_get_optional_int_env("QUEUES_TERMINAL_RETENTION_SECONDS")
    )
    ENABLE_PROMETHEUS: bool = field(default_factory=get_env("QUEUES_ENABLE_PROMETHEUS", False))
    WORKER_WAKEUPS: bool | None = field(default_factory=_get_optional_bool_env("QUEUES_WORKER_WAKEUPS"))

    def resolve_worker_wakeups(self, db_settings: DatabaseSettings) -> bool:
        """Resolve whether PostgreSQL LISTEN/NOTIFY worker wakeups should be enabled.

        Wakeups are always disabled for non-PostgreSQL dialects such as SQLite.
        """
        if not db_settings.is_postgres():
            return False
        if self.WORKER_WAKEUPS is None:
            return True
        return self.WORKER_WAKEUPS

    def get_config(
        self,
        *,
        alchemy_config: SQLAlchemyAsyncConfig,
        db_settings: DatabaseSettings,
        app_settings: AppSettings | None = None,
    ) -> QueueConfig:
        """Build the ``litestar-queues`` configuration bound to PostgreSQL via Advanced Alchemy."""
        from litestar_queues.backends.advanced_alchemy import (
            QueueEventHistoryModel,
            QueueMaintenanceModel,
            QueueTaskModel,
            QueueTaskReservationModel,
        )

        backend = SQLAlchemyBackendConfig(
            sqlalchemy_config=alchemy_config,
            model_class=QueueTaskModel,
            event_history_model_class=QueueEventHistoryModel,
            maintenance_model_class=QueueMaintenanceModel,
            task_reservation_model_class=QueueTaskReservationModel,
            worker_wakeups=self.resolve_worker_wakeups(db_settings),
        )
        worker = WorkerConfig(
            placement=cast("WorkerPlacement", self.PLACEMENT),
            max_concurrency=self.MAX_CONCURRENCY,
            batch_size=self.BATCH_SIZE,
            poll_interval=self.POLL_INTERVAL,
            queues=self.QUEUES,
        )
        maintenance = QueueMaintenanceConfig(
            terminal_retention=(
                float(self.TERMINAL_RETENTION_SECONDS) if self.TERMINAL_RETENTION_SECONDS is not None else None
            ),
        )
        observability = ObservabilityConfig(
            enable_otel=app_settings.ENABLE_INSTRUMENTATION if app_settings is not None else False,
            enable_prometheus=self.ENABLE_PROMETHEUS,
        )
        events = QueueEventsConfig(
            delivery=EventDeliveryConfig(),
            stream=EventStreamConfig(path=self.STREAM_PATH) if self.STREAM_ENABLED else None,
            history=EventHistoryConfig(),
        )
        return QueueConfig(
            queue_backend=backend,
            execution_backend=cast("ExecutionBackendConfig", self.EXECUTION_BACKEND),
            worker=worker,
            maintenance=maintenance,
            observability=observability,
            events=events,
        )


@dataclass
class SecuritySettings:
    """Declarative ``litestar-security`` settings and HKDF subkey derivation helpers."""

    COOKIE_SECURE: bool = field(default_factory=get_env("COOKIE_SECURE", False))
    SESSION_MAX_AGE: int = field(default_factory=get_env("SESSION_MAX_AGE", 60 * 60 * 24 * 14))
    MFA_ISSUER: str = field(default_factory=get_env("MFA_ISSUER", "Litestar Fullstack"))
    PASSKEY_RP_ID: str = field(default_factory=get_env("PASSKEY_RP_ID", "localhost"))
    PASSKEY_RP_NAME: str = field(default_factory=get_env("PASSKEY_RP_NAME", "Litestar Fullstack"))
    PASSKEY_ORIGINS: list[str] = field(
        default_factory=get_env("PASSKEY_ORIGINS", ["http://localhost:8000", "http://localhost:5173"])
    )
    REGISTRATION_REQUIRE_VERIFICATION: bool = field(
        default_factory=get_env("REGISTRATION_REQUIRE_VERIFICATION", False)
    )

    def derive_key(self, app_settings: AppSettings, info: bytes, *, length: int = 32) -> bytes:
        """Derive a purpose-isolated HKDF-SHA256 subkey from ``app_settings.SECRET_KEY``."""
        return derive_subkey(app_settings.SECRET_KEY, info, length=length)

    def get_config(self, app_settings: AppSettings) -> SecurityConfig[Any]:
        """Build baseline hardened ``SecurityConfig`` excluding only static assets."""
        _ = app_settings
        return SecurityConfig(
            headers=SecurityHeadersConfig.hardened(),
            exclude=["^/static"],
        )


@dataclass
class MCPSettings:
    """Model Context Protocol plugin configuration settings."""

    ENABLED: bool = field(default_factory=get_env("MCP_ENABLED", True))
    BASE_PATH: str = field(default_factory=get_env("MCP_BASE_PATH", "/mcp"))
    NAME: str = field(default_factory=get_env("MCP_NAME", "Litestar Fullstack MCP"))
    INSTRUCTIONS: str = field(
        default_factory=get_env(
            "MCP_INSTRUCTIONS",
            "Authenticated Model Context Protocol surface for Litestar Fullstack.",
        )
    )
    ALLOWED_ORIGINS: list[str] | None = field(default_factory=_get_optional_list_env("MCP_ALLOWED_ORIGINS"))

    def get_config(self, *, auth: Any | None = None) -> MCPConfig:
        """Build ``MCPConfig`` with optional authentication binding."""
        return MCPConfig(
            base_path=self.BASE_PATH,
            name=self.NAME,
            instructions=self.INSTRUCTIONS,
            allowed_origins=self.ALLOWED_ORIGINS,
            auth=auth,
            include_in_schema=False,
            auto_output_schema=True,
        )


@dataclass
class ViteSettings:
    """Vite build and TypeGen configuration settings."""

    DEV_MODE: bool = field(default_factory=get_env("VITE_DEV_MODE", False))
    BUNDLE_DIR: Path = field(default_factory=get_env("VITE_BUNDLE_DIR", STATIC_DIR))
    ASSET_URL: str = field(default_factory=get_env("ASSET_URL", "/static/"))
    TRUSTED_PROXIES: str | None = field(default_factory=get_env("LITESTAR_TRUSTED_PROXIES", None))

    def get_config(self, base_dir: Path = BASE_DIR.parent.parent) -> ViteConfig:
        """Build ``ViteConfig`` with SPA mode and full TypeGen including AsyncAPI channels."""
        js_home = base_dir / "js" / "web"
        return ViteConfig(
            mode="spa",
            dev_mode=self.DEV_MODE,
            runtime=RuntimeConfig(executor="bun", trusted_proxies=self.TRUSTED_PROXIES),
            paths=PathConfig(
                root=js_home,
                bundle_dir=self.BUNDLE_DIR,
                asset_url=self.ASSET_URL,
            ),
            types=TypeGenConfig(
                output=Path("src/lib/generated"),
                generate_sdk=True,
                generate_routes=True,
                generate_schemas=True,
                generate_channels=True,
            ),
        )


@dataclass
class ServerSettings:
    """ASGI server and proxy header configuration."""

    APP_LOC: str = "app.server.asgi:create_app"
    HOST: str = field(default_factory=get_env("LITESTAR_HOST", "0.0.0.0"))  # noqa: S104
    PORT: int = field(default_factory=get_env("LITESTAR_PORT", 8000))
    KEEPALIVE: int = field(default_factory=get_env("LITESTAR_KEEPALIVE", 65))
    RELOAD: bool = field(default_factory=get_env("LITESTAR_RELOAD", False))
    RELOAD_DIRS: list[str] = field(default_factory=get_env("LITESTAR_RELOAD_DIRS", [f"{BASE_DIR}"]))
    LITESTAR_TRUSTED_PROXIES: list[str] = field(default_factory=_get_list_env("LITESTAR_TRUSTED_PROXIES", []))


@dataclass
class EmailSettings:
    """Transactional email backend configuration."""

    BACKEND: str = field(default_factory=get_env("EMAIL_BACKEND", "console"))
    FROM_EMAIL: str = field(default_factory=get_env("EMAIL_FROM_ADDRESS", "noreply@localhost"))
    FROM_NAME: str = field(default_factory=get_env("EMAIL_FROM_NAME", "Litestar App"))
    SMTP_HOST: str = field(default_factory=get_env("EMAIL_SMTP_HOST", "localhost"))
    SMTP_PORT: int = field(default_factory=get_env("EMAIL_SMTP_PORT", 587, int))
    SMTP_USER: str = field(default_factory=get_env("EMAIL_SMTP_USER", ""))
    SMTP_PASSWORD: str = field(default_factory=get_env("EMAIL_SMTP_PASSWORD", ""))
    USE_TLS: bool = field(default_factory=get_env("EMAIL_USE_TLS", True))
    USE_SSL: bool = field(default_factory=get_env("EMAIL_USE_SSL", False))
    TIMEOUT: int = field(default_factory=get_env("EMAIL_TIMEOUT", 30, int))
    RESEND_API_KEY: str = field(default_factory=get_env("RESEND_API_KEY", ""))

    def get_config(self) -> EmailConfig:
        """Build ``EmailConfig`` for ``litestar-email``."""
        backend: str | SMTPConfig | ResendConfig = self.BACKEND
        if self.BACKEND == "smtp":
            backend = SMTPConfig(
                host=self.SMTP_HOST,
                port=self.SMTP_PORT,
                username=self.SMTP_USER,
                password=self.SMTP_PASSWORD,
                use_tls=self.USE_TLS,
                use_ssl=self.USE_SSL,
                timeout=self.TIMEOUT,
            )
        elif self.BACKEND == "resend":
            backend = ResendConfig(api_key=self.RESEND_API_KEY)
        return EmailConfig(
            backend=backend,
            from_email=self.FROM_EMAIL,
            from_name=self.FROM_NAME,
        )


@dataclass
class AppSettings:
    """General application metadata, CORS, OAuth, and secret key configuration."""

    NAME: str = field(default_factory=lambda: "Litestar Fullstack Template")
    VERSION: str = field(default=f"v{current_version}")
    CONTACT_NAME: str = field(default="Admin")
    CONTACT_EMAIL: str = field(default="admin@localhost")
    URL: str = field(default_factory=get_env("APP_URL", "http://localhost:8000"))
    DEBUG: bool = field(default_factory=get_env("LITESTAR_DEBUG", False))
    SECRET_KEY: str = field(
        default_factory=get_env("SECRET_KEY", binascii.hexlify(os.urandom(32)).decode(encoding="utf-8")),
    )
    ALLOWED_CORS_ORIGINS: list[str] | str = field(default_factory=get_env("ALLOWED_CORS_ORIGINS", ["*"], list[str]))
    COOKIE_SECURE: bool = field(default_factory=get_env("COOKIE_SECURE", False))
    STATIC_DIR: Path = field(default_factory=get_env("STATIC_DIR", STATIC_DIR))
    STATIC_URL: str = field(default_factory=get_env("STATIC_URL", "/static/web/"))
    BASE_URL: str | None = None
    DEV_MODE: bool = field(default_factory=get_env("VITE_DEV_MODE", False))
    ENABLE_INSTRUMENTATION: bool = False
    GOOGLE_OAUTH2_CLIENT_ID: str = field(default_factory=get_env("GOOGLE_OAUTH2_CLIENT_ID", ""))
    GOOGLE_OAUTH2_CLIENT_SECRET: str = field(default_factory=get_env("GOOGLE_OAUTH2_CLIENT_SECRET", ""))
    GITHUB_OAUTH2_CLIENT_ID: str = field(default_factory=get_env("GITHUB_OAUTH2_CLIENT_ID", ""))
    GITHUB_OAUTH2_CLIENT_SECRET: str = field(default_factory=get_env("GITHUB_OAUTH2_CLIENT_SECRET", ""))
    ENV_SECRETS: str = field(default_factory=get_env("ENV_SECRETS", "runtime-secrets"))

    @property
    def google_oauth_enabled(self) -> bool:
        """Return whether Google OAuth credentials are configured."""
        return bool(self.GOOGLE_OAUTH2_CLIENT_ID and self.GOOGLE_OAUTH2_CLIENT_SECRET)

    @property
    def github_oauth_enabled(self) -> bool:
        """Return whether GitHub OAuth credentials are configured."""
        return bool(self.GITHUB_OAUTH2_CLIENT_ID and self.GITHUB_OAUTH2_CLIENT_SECRET)

    @property
    def slug(self) -> str:
        """Return a slugified form of the application name."""
        return slugify(self.NAME)

    def get_compression_config(self) -> CompressionConfig:
        """Return HTTP response compression configuration."""
        return CompressionConfig(backend="gzip")

    def get_cors_config(self) -> CORSConfig:
        """Return CORS configuration."""
        return CORSConfig(allow_origins=cast("list[str]", self.ALLOWED_CORS_ORIGINS), allow_credentials=True)

    def get_problem_details_config(self) -> ProblemDetailsConfig:
        """Return RFC 9457 Problem Details configuration."""
        return ProblemDetailsConfig(enable_for_all_http_exceptions=True)

    def __post_init__(self) -> None:
        if isinstance(self.ALLOWED_CORS_ORIGINS, str):
            if self.ALLOWED_CORS_ORIGINS.startswith("[") and self.ALLOWED_CORS_ORIGINS.endswith("]"):
                try:
                    self.ALLOWED_CORS_ORIGINS = json.loads(self.ALLOWED_CORS_ORIGINS)  # pyright: ignore[reportConstantRedefinition]
                except (SyntaxError, ValueError):
                    msg = "ALLOWED_CORS_ORIGINS is not a valid list representation."
                    raise ValueError(msg) from None
            else:
                self.ALLOWED_CORS_ORIGINS = [host.strip() for host in self.ALLOWED_CORS_ORIGINS.split(",")]  # pyright: ignore[reportConstantRedefinition]


@dataclass
class LogSettings:
    """Structured logging configuration."""

    EXCLUDE_PATHS: str = r"\A(?!x)x"
    INCLUDE_COMPRESSED_BODY: bool = False
    LEVEL: int = field(default_factory=get_env("LOG_LEVEL", 30))
    OBFUSCATE_COOKIES: set[str] = field(
        default_factory=lambda: {
            "session",
            "XSRF-TOKEN",
            "__Host-app-session",
            "__Host-app-binding",
            "app-session",
            "app-binding",
        }
    )
    OBFUSCATE_HEADERS: set[str] = field(default_factory=lambda: {"Authorization", "X-API-KEY", "X-XSRF-TOKEN"})
    REQUEST_FIELDS: list[RequestExtractorField] = field(
        default_factory=get_env(
            "LOG_REQUEST_FIELDS",
            ["path", "method", "query", "path_params"],
            list[RequestExtractorField],
        ),
    )
    RESPONSE_FIELDS: list[ResponseExtractorField] = field(
        default_factory=get_env(
            "LOG_RESPONSE_FIELDS",
            ["status_code"],
            type_hint=list[ResponseExtractorField],
        )
    )
    QUEUES_LEVEL: int = field(default_factory=get_env("QUEUES_LOG_LEVEL", 30))
    SQLALCHEMY_LEVEL: int = field(default_factory=get_env("SQLALCHEMY_LOG_LEVEL", 30))
    ASGI_ACCESS_LEVEL: int = field(default_factory=get_env("ASGI_ACCESS_LOG_LEVEL", 30))
    ASGI_ERROR_LEVEL: int = field(default_factory=get_env("ASGI_ERROR_LOG_LEVEL", 30))

    def get_structlog_config(self) -> StructlogConfig:
        """Build Litestar ``StructlogConfig`` with ``litestar_queues`` and Granian loggers."""
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
                        "litestar_queues": {
                            "propagate": False,
                            "level": self.QUEUES_LEVEL,
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
                request_cookies_to_obfuscate=self.OBFUSCATE_COOKIES,
                request_headers_to_obfuscate=self.OBFUSCATE_HEADERS,
                response_cookies_to_obfuscate=self.OBFUSCATE_COOKIES,
                response_headers_to_obfuscate=self.OBFUSCATE_HEADERS,
            ),
        )


@dataclass
class Settings:
    """Top-level application settings aggregate."""

    app: AppSettings = field(default_factory=AppSettings)
    db: DatabaseSettings = field(default_factory=DatabaseSettings)
    vite: ViteSettings = field(default_factory=ViteSettings)
    server: ServerSettings = field(default_factory=ServerSettings)
    queues: QueueSettings = field(default_factory=QueueSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    mcp: MCPSettings = field(default_factory=MCPSettings)
    log: LogSettings = field(default_factory=LogSettings)
    email: EmailSettings = field(default_factory=EmailSettings)

    @classmethod
    @lru_cache(maxsize=1, typed=True)
    def from_env(cls, dotenv_filename: str = ".env") -> Settings:
        """Load settings from optional ``.env`` file and process environment."""
        logger = structlog.get_logger()
        env_file = Path(f"{os.curdir}/{dotenv_filename}")
        if env_file.is_file():
            console.print(f"[yellow]Loading environment configuration from {dotenv_filename}[/]")
            load_dotenv(env_file, override=False)
        try:
            app = AppSettings()
            db = DatabaseSettings()
            vite = ViteSettings()
            server = ServerSettings()
            queues = QueueSettings()
            security = SecuritySettings()
            mcp = MCPSettings()
            log = LogSettings()
            email = EmailSettings()
        except Exception as exc:  # noqa: BLE001
            logger.fatal("Could not load settings. %s", exc)
            sys.exit(1)
        return Settings(
            app=app,
            db=db,
            vite=vite,
            server=server,
            queues=queues,
            security=security,
            mcp=mcp,
            log=log,
            email=email,
        )


def get_settings(dotenv_filename: str = ".env") -> Settings:
    """Return cached top-level settings."""
    return Settings.from_env(dotenv_filename)


def provide_app_settings() -> AppSettings:
    """Return application settings for Litestar dependency injection."""
    return get_settings().app
