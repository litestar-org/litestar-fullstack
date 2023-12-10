from __future__ import annotations

import importlib
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Final, Literal

from dotenv import load_dotenv
from litestar.data_extractors import RequestExtractorField, ResponseExtractorField  # noqa: TCH002
from pydantic import ValidationError, field_validator
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

from app import utils

__all__ = [
    "DatabaseSettings",
    "AppSettings",
    "OpenAPISettings",
    "RedisSettings",
    "LogSettings",
    "WorkerSettings",
    "ServerSettings",
    "app",
    "db",
    "openapi",
    "redis",
    "server",
    "log",
    "worker",
]

DEFAULT_MODULE_NAME = "app"
BASE_DIR: Final = utils.module_to_os_path(DEFAULT_MODULE_NAME)
RESOURCES_DIR = Path(BASE_DIR / "domain" / "web" / "resources")
STATIC_DIR = Path(BASE_DIR / "domain" / "web" / "public")
TEMPLATES_DIR = Path(BASE_DIR / "domain" / "web" / "templates")
version = importlib.metadata.version(DEFAULT_MODULE_NAME)


class ServerSettings(BaseSettings):
    """Server configurations."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SERVER_",
        case_sensitive=False,
    )

    APP_LOC: str = "app.asgi:create_app"
    """Path to app executable, or factory."""
    APP_LOC_IS_FACTORY: bool = True
    """Indicate if APP_LOC points to an executable or factory."""
    HOST: str = "localhost"
    """Server network host."""
    KEEPALIVE: int = 65
    """Seconds to hold connections open (65 is > AWS lb idle timeout)."""
    PORT: int = 8000
    """Server port."""
    RELOAD: bool | None = None
    """Turn on hot reloading."""
    RELOAD_DIRS: list[str] = [f"{BASE_DIR}"]
    """Directories to watch for reloading."""
    HTTP_WORKERS: int | None = None
    """Number of HTTP Worker processes to be spawned by Uvicorn."""


class AppSettings(BaseSettings):
    """Generic application settings.

    These settings are returned as json by the healthcheck endpoint, so
    do not include any sensitive values here, or if you do ensure to
    exclude them from serialization in the `model_config` object.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        case_sensitive=False,
    )

    BUILD_NUMBER: str = ""
    """Identifier for CI build."""
    DEBUG: bool = False
    """Run `Litestar` with `debug=True`."""
    ENVIRONMENT: str = "prod"
    """'dev', 'prod', etc."""
    TEST_ENVIRONMENT_NAME: str = "test"
    """Value of ENVIRONMENT used to determine if running tests.

    This should be the value of `ENVIRONMENT` in `tests.env`.
    """
    LOCAL_ENVIRONMENT_NAME: str = "local"
    """Value of ENVIRONMENT used to determine if running in local development
    mode.

    This should be the value of `ENVIRONMENT` in your local `.env` file.
    """
    NAME: str = "app"
    """Application name."""
    SECRET_KEY: str
    """Number of HTTP Worker processes to be spawned by Uvicorn."""
    JWT_ENCRYPTION_ALGORITHM: str = "HS256"
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    STATIC_URL: str = "/static/"
    CSRF_COOKIE_NAME: str = "csrftoken"
    CSRF_COOKIE_SECURE: bool = False
    """Default URL where static assets are located."""
    STATIC_DIR: Path = STATIC_DIR
    DEV_MODE: bool = False

    @property
    def slug(self) -> str:
        """Return a slugified name.

        Returns:
            `self.NAME`, all lowercase and hyphens instead of spaces.
        """
        return utils.slugify(self.NAME)

    @field_validator("BACKEND_CORS_ORIGINS")
    def assemble_cors_origins(
        cls,
        value: str | list[str],
    ) -> list[str] | str:
        """Parse a list of origins."""
        if isinstance(value, list):
            return value
        if isinstance(value, str) and not value.startswith("["):
            return [host.strip() for host in value.split(",")]
        if isinstance(value, str) and value.startswith("[") and value.endswith("]"):
            return list(value)
        raise ValueError(value)

    @field_validator("SECRET_KEY")
    def generate_secret_key(
        cls,
        value: str | None,
    ) -> str:
        """Generate a secret key."""
        return os.urandom(32).decode() if value is None else value


class LogSettings(BaseSettings):
    """Logging config for the application."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", env_prefix="LOG_")

    # https://stackoverflow.com/a/1845097/6560549
    EXCLUDE_PATHS: str = r"\A(?!x)x"
    """Regex to exclude paths from logging."""
    HTTP_EVENT: str = "HTTP"
    """Log event name for logs from Litestar handlers."""
    INCLUDE_COMPRESSED_BODY: bool = False
    """Include 'body' of compressed responses in log output."""
    LEVEL: int = 20
    """Stdlib log levels.

    Only emit logs at this level, or higher.
    """
    OBFUSCATE_COOKIES: set[str] = {"session"}
    """Request cookie keys to obfuscate."""
    OBFUSCATE_HEADERS: set[str] = {"Authorization", "X-API-KEY"}
    """Request header keys to obfuscate."""
    JOB_FIELDS: list[str] = [
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
    ]
    """Attributes of the SAQ.

    [`Job`](https://github.com/tobymao/saq/blob/master/saq/job.py) to be
    logged.
    """
    REQUEST_FIELDS: list[RequestExtractorField] = [
        "path",
        "method",
        "headers",
        "cookies",
        "query",
        "path_params",
        "body",
    ]
    """Attributes of the [Request][litestar.connection.request.Request] to be
    logged."""
    RESPONSE_FIELDS: list[ResponseExtractorField] = [
        "status_code",
        "cookies",
        "headers",
        "body",
    ]
    """Attributes of the [Response][litestar.response.Response] to be
    logged."""
    WORKER_EVENT: str = "Worker"
    """Log event name for logs from SAQ worker."""
    SAQ_LEVEL: int = 20
    """Level to log SAQ logs."""
    SQLALCHEMY_LEVEL: int = 30
    """Level to log SQLAlchemy logs."""
    UVICORN_ACCESS_LEVEL: int = 30
    """Level to log uvicorn access logs."""
    UVICORN_ERROR_LEVEL: int = 20
    """Level to log uvicorn error logs."""


# noinspection PyUnresolvedReferences
class OpenAPISettings(BaseSettings):
    """Configures OpenAPI for the application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="OPENAPI_",
        case_sensitive=False,
    )

    CONTACT_NAME: str = "Cody"
    """Name of contact on document."""
    CONTACT_EMAIL: str = "admin"
    """Email for contact on document."""
    TITLE: str | None = "Litestar Fullstack"
    """Document title."""
    VERSION: str = f"v{version}"
    """Document version."""


class WorkerSettings(BaseSettings):
    """Global SAQ Job configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="WORKER_",
        case_sensitive=False,
    )

    CONCURRENCY: int = 10
    """The number of concurrent jobs allowed to execute per worker.

    Default is set to 10.
    """
    WEB_ENABLED: bool = True
    """If true, the worker admin UI is launched on worker startup.."""
    """Initialization method for the worker process."""


class DatabaseSettings(BaseSettings):
    """Configures the database for the application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DB_",
        case_sensitive=False,
    )

    ECHO: bool = False
    """Enable SQLAlchemy engine logs."""
    ECHO_POOL: bool | Literal["debug"] = False
    """Enable SQLAlchemy connection pool logs."""
    POOL_DISABLE: bool = False
    """Disable SQLAlchemy pooling, same as setting pool to.

    [`NullPool`][sqlalchemy.pool.NullPool].
    """
    POOL_MAX_OVERFLOW: int = 10
    """See [`max_overflow`][sqlalchemy.pool.QueuePool]."""
    POOL_SIZE: int = 5
    """See [`pool_size`][sqlalchemy.pool.QueuePool]."""
    POOL_TIMEOUT: int = 30
    """See [`timeout`][sqlalchemy.pool.QueuePool]."""
    POOL_RECYCLE: int = 300
    POOL_PRE_PING: bool = False
    CONNECT_ARGS: dict[str, Any] = {}
    URL: str = "postgresql+asyncpg://postgres:mysecretpassword@localhost:5432/postgres"
    ENGINE: str | None = None
    USER: str | None = None
    PASSWORD: str | None = None
    HOST: str | None = None
    PORT: int | None = None
    NAME: str | None = None
    MIGRATION_CONFIG: str = f"{BASE_DIR}/lib/db/alembic.ini"
    MIGRATION_PATH: str = f"{BASE_DIR}/lib/db/migrations"
    MIGRATION_DDL_VERSION_TABLE: str = "ddl_version"


class RedisSettings(BaseSettings):
    """Redis settings for the application."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", env_prefix="REDIS_")

    URL: str = "redis://localhost:6379/0"
    """A Redis connection URL."""
    DB: int | None = None
    """Redis DB ID (optional)"""
    PORT: int | None = None
    """Redis port (optional)"""
    SOCKET_CONNECT_TIMEOUT: int = 5
    """Length of time to wait (in seconds) for a connection to become
    active."""
    HEALTH_CHECK_INTERVAL: int = 5
    """Length of time to wait (in seconds) before testing connection health."""
    SOCKET_KEEPALIVE: int = 5
    """Length of time to wait (in seconds) between keepalive commands."""


@lru_cache
def load_settings() -> (
    tuple[
        AppSettings,
        RedisSettings,
        DatabaseSettings,
        OpenAPISettings,
        ServerSettings,
        LogSettings,
        WorkerSettings,
    ]
):
    """Load Settings file.

    As an example, I've commented on how you might go about injecting secrets into the environment for production.

    This fetches a ``.env`` configuration from a Google secret and configures the environment with those variables.

    .. code-block:: python

        secret_id = os.environ.get("ENV_SECRETS", None)
        env_file_exists = os.path.isfile(f"{os.curdir}/.env")
        local_service_account_exists = os.path.isfile(f"{os.curdir}/service_account.json")
        if local_service_account_exists:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"
        project_id = os.environ.get("GOOGLE_PROJECT_ID", None)
        if project_id is None:
            _, project_id = google.auth.default()
            os.environ["GOOGLE_PROJECT_ID"] = project_id
        if not env_file_exists and secret_id:
            secret = secret_manager.get_secret(project_id, secret_id)
            load_dotenv(stream=io.StringIO(secret))

        try:
            settings = ...  # existing code below
        except:
            ...
        return settings

    Returns:
        Settings: application settings
    """
    env_file = Path(f"{os.curdir}/.env")
    if env_file.is_file():
        load_dotenv(env_file)
    try:
        """Override Application reload dir."""
        server: ServerSettings = ServerSettings(
            HOST="0.0.0.0",  # noqa: S104
            RELOAD_DIRS=[str(BASE_DIR)],
        )
        app: AppSettings = AppSettings()
        redis: RedisSettings = RedisSettings()
        db: DatabaseSettings = DatabaseSettings()
        openapi: OpenAPISettings = OpenAPISettings()
        log: LogSettings = LogSettings()
        worker: WorkerSettings = WorkerSettings()

    except ValidationError as e:
        print("Could not load settings.", e)  # noqa: T201
        raise
    return (
        app,
        redis,
        db,
        openapi,
        server,
        log,
        worker,
    )


(
    app,
    redis,
    db,
    openapi,
    server,
    log,
    worker,
) = load_settings()
