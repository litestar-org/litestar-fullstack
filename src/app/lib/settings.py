from __future__ import annotations

import binascii
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Final, Literal

from pydantic import AnyUrl, BaseSettings, PostgresDsn, SecretBytes, ValidationError, parse_obj_as, validator
from starlite.data_extractors import RequestExtractorField, ResponseExtractorField  # noqa: TCH002

from app import utils

__all__ = [
    "DatabaseSettings",
    "APISettings",
    "AppSettings",
    "OpenAPISettings",
    "RedisSettings",
    "LogSettings",
    "WorkerSettings",
    "HTTPClientSettings",
    "ServerSettings",
    "app",
    "api",
    "db",
    "openapi",
    "redis",
    "server",
    "log",
    "worker",
    "http_client",
]

DEFAULT_MODULE_NAME = "app"
BASE_DIR: Final = utils.module_to_os_path(DEFAULT_MODULE_NAME)
STATIC_DIR = Path(BASE_DIR / "domain" / "web" / "public")
TEMPLATES_DIR = Path(BASE_DIR / "domain" / "web" / "templates")


class ServerSettings(BaseSettings):
    """Server configurations."""

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_prefix = "SERVER_"

    APP_LOC: str = "app.asgi:app"
    """Path to app executable, or factory."""
    APP_LOC_IS_FACTORY: bool = False
    """Indicate if APP_LOC points to an executable or factory."""
    HOST: str = "localhost"
    """Server network host."""
    KEEPALIVE: int = 65
    """Seconds to hold connections open (65 is > AWS lb idle timeout)."""
    PORT: int = 8000
    """Server port."""
    RELOAD: bool | None = None
    """Turn on hot reloading."""
    RELOAD_DIRS: list[str] = ["src/"]
    """Directories to watch for reloading."""
    HTTP_WORKERS: int | None = None
    """Number of HTTP Worker processes to be spawned by Uvicorn."""


class AppSettings(BaseSettings):
    """Generic application settings.

    These settings are returned as json by the healthcheck endpoint, so
    do not include any sensitive values here, or if you do ensure to
    exclude them from serialization in the `Config` object.
    """

    class Config:
        case_sensitive = True
        env_file = ".env"

    BUILD_NUMBER: str = ""
    """Identifier for CI build."""
    CHECK_DB_READY: bool = True
    """Check for database readiness on startup."""
    CHECK_REDIS_READY: bool = True
    """Check for redis readiness on startup."""
    DEBUG: bool = False
    """Run `Starlite` with `debug=True`."""
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
    SECRET_KEY: SecretBytes
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
        return "-".join(s.lower() for s in self.NAME.split())

    @validator("BACKEND_CORS_ORIGINS", pre=True)
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

    @validator("SECRET_KEY", pre=True, always=True)
    def generate_secret_key(
        cls,
        value: SecretBytes | None,
    ) -> SecretBytes:
        """Generate a secret key."""
        if value is None:
            return SecretBytes(binascii.hexlify(os.urandom(32)))
        return value


class APISettings(BaseSettings):
    """API specific configuration."""

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_prefix = "API_"

    CACHE_EXPIRATION: int = 60
    """Default cache key expiration in seconds."""
    DB_SESSION_DEPENDENCY_KEY: str = "db_session"
    """Parameter name for SQLAlchemy session dependency injection."""
    DEFAULT_PAGINATION_LIMIT: int = 100
    """Max records received for collection routes."""
    DTO_INFO_KEY: str = "dto"
    """Key used for DTO field config in SQLAlchemy info dict."""
    HEALTH_PATH: str = "/health"
    """Route that the health check is served under."""


class LogSettings(BaseSettings):
    """Logging config for the application."""

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_prefix = "LOG_"

    # https://stackoverflow.com/a/1845097/6560549
    EXCLUDE_PATHS: str = r"\A(?!x)x"
    """Regex to exclude paths from logging."""
    HTTP_EVENT: str = "HTTP"
    """Log event name for logs from Starlite handlers."""
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
    """Attributes of the [Request][starlite.connection.request.Request] to be
    logged."""
    RESPONSE_FIELDS: list[ResponseExtractorField] = [
        "status_code",
        "cookies",
        "headers",
        "body",
    ]
    """Attributes of the [Response][starlite.response.Response] to be
    logged."""
    WORKER_EVENT: str = "Worker"
    """Log event name for logs from SAQ worker."""
    SAQ_LEVEL: int = 30
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

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_prefix = "OPENAPI_"

    CONTACT_NAME: str = "Peter"
    """Name of contact on document."""
    CONTACT_EMAIL: str = "peter.github@proton.me"
    """Email for contact on document."""
    TITLE: str | None = "My Starlite-SAQAlchemy App"
    """Document title."""
    VERSION: str = "v1.0"
    """Document version."""


class HTTPClientSettings(BaseSettings):
    """HTTP Client configurations."""

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_prefix = "HTTP_"

    BACKOFF_MAX: float = 60
    BACKOFF_MIN: float = 0
    EXPONENTIAL_BACKOFF_BASE: float = 2
    EXPONENTIAL_BACKOFF_MULTIPLIER: float = 1


class WorkerSettings(BaseSettings):
    """Global SAQ Job configuration."""

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_prefix = "WORKER_"

    JOB_TIMEOUT: int = 10
    """Max time a job can run for, in seconds.

    Set to `0` for no timeout.
    """
    JOB_HEARTBEAT: int = 0
    """Max time a job can survive without emitting a heartbeat. `0` to disable.

    `job.update()` will trigger a heartbeat.
    """
    JOB_RETRIES: int = 10
    """Max attempts for any job."""
    JOB_TTL: int = 600
    """Lifetime of available job information, in seconds.

    0: indefinite
    -1: disabled (no info retained)
    """
    JOB_RETRY_DELAY: float = 1.0
    """Seconds to delay before retrying a job."""
    JOB_RETRY_BACKOFF: bool | float = 60
    """If true, use exponential backoff for retry delays.

    - The first retry will have whatever retry_delay is.
    - The second retry will have retry_delay*2. The third retry will have retry_delay*4. And so on.
    - This always includes jitter, where the final retry delay is a random number between 0 and the calculated retry delay.
    - If retry_backoff is set to a number, that number is the maximum retry delay, in seconds."
    """
    CONCURRENCY: int = 10
    """The number of concurrent jobs allowed to execute per worker.

    Default is set to 10.
    """
    WEB_ENABLED: bool = False
    """If true, the worker admin UI is launched on worker startup.."""
    WEB_PORT: int = 8081
    """Port to use for the worker web UI."""
    INIT_METHOD: Literal["integrated", "standalone"] = "integrated"
    """Initialization method for the worker process."""


class DatabaseSettings(BaseSettings):
    """Configures the database for the application."""

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_prefix = "DB_"

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
    POOL_PRE_PING: bool = True
    CONNECT_ARGS: dict[str, Any] = {}
    URL: PostgresDsn = parse_obj_as(
        PostgresDsn,
        "postgresql+asyncpg://postgres:mysecretpassword@localhost:5432/postgres",
    )

    DB_ENGINE: str | None = None
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None
    DB_HOST: str | None = None
    DB_PORT: str | None = None
    DB_NAME: str | None = None
    MIGRATION_CONFIG: str = f"{BASE_DIR}/lib/db/alembic.ini"
    MIGRATION_PATH: str = f"{BASE_DIR}/lib/db/migrations"
    MIGRATION_DDL_VERSION_TABLE: str = "ddl_version"


class RedisSettings(BaseSettings):
    """Redis settings for the application."""

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_prefix = "REDIS_"

    URL: AnyUrl = parse_obj_as(AnyUrl, "redis://localhost:6379/0")
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
        APISettings,
        RedisSettings,
        DatabaseSettings,
        OpenAPISettings,
        ServerSettings,
        LogSettings,
        HTTPClientSettings,
        WorkerSettings,
    ]
):
    """Load Settings file.

    As an example, I've commented out how you might go about injecting secrets into the environment for production.

    This fetches a `.env` configuration from a Google secret and configures the environment with those variables.

    ```python
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
    ```
    Returns:
        Settings: application settings
    """
    try:
        """Override Application reload dir."""
        server: ServerSettings = ServerSettings.parse_obj(
            {"HOST": "0.0.0.0", "RELOAD_DIRS": [str(BASE_DIR)]},  # noqa: S104
        )
        app: AppSettings = AppSettings.parse_obj({})
        api: APISettings = APISettings.parse_obj({})
        redis: RedisSettings = RedisSettings.parse_obj({})
        db: DatabaseSettings = DatabaseSettings.parse_obj({})
        openapi: OpenAPISettings = OpenAPISettings.parse_obj({})
        log: LogSettings = LogSettings.parse_obj({})
        worker: WorkerSettings = WorkerSettings.parse_obj({})
        http_client: HTTPClientSettings = HTTPClientSettings.parse_obj({})

    except ValidationError as e:
        print("Could not load settings. %s", e)  # noqa: T201
        raise e from e
    return (
        app,
        api,
        redis,
        db,
        openapi,
        server,
        log,
        http_client,
        worker,
    )


(
    app,
    api,
    redis,
    db,
    openapi,
    server,
    log,
    http_client,
    worker,
) = load_settings()
