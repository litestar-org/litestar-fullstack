from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Final, Literal

from pydantic import BaseSettings, ValidationError
from starlite_saqlalchemy.settings import (
    APISettings,
    AppSettings,
    HTTPClientSettings,
    LogSettings,
    OpenAPISettings,
    RedisSettings,
)
from starlite_saqlalchemy.settings import DatabaseSettings as _DatabaseSettings
from starlite_saqlalchemy.settings import ServerSettings as _ServerSettings
from starlite_saqlalchemy.settings import WorkerSettings as _WorkerSettings
from starlite_saqlalchemy.settings import api as api_settings
from starlite_saqlalchemy.settings import app as app_settings
from starlite_saqlalchemy.settings import http as http_client_settings
from starlite_saqlalchemy.settings import log as log_settings
from starlite_saqlalchemy.settings import openapi as openapi_settings
from starlite_saqlalchemy.settings import redis as redis_settings
from starlite_saqlalchemy.settings import server as server_settings
from starlite_saqlalchemy.settings import worker as worker_settings

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
BASE_DIR: Final = utils.module_loader.module_to_os_path(DEFAULT_MODULE_NAME)
PUBLIC_DIR = Path(BASE_DIR / "api" / "public")


class ServerSettings(_ServerSettings):
    """Server Settings."""

    HTTP_WORKERS: int | None = None
    """Number of HTTP Worker processes to be spawned by Uvicorn."""


class WorkerSettings(_WorkerSettings):
    """Worker Settings."""

    INIT_METHOD: Literal["in-process", "standalone"] = "in-process"
    PROCESSES: int = 1
    CONCURRENCY: int = 10


class DatabaseSettings(_DatabaseSettings):
    """Database Settings."""

    DB_ENGINE: str | None = None
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None
    DB_HOST: str | None = None
    DB_PORT: str | None = None
    DB_NAME: str | None = None
    MIGRATION_CONFIG: str = f"{BASE_DIR}/lib/db/alembic.ini"
    MIGRATION_PATH: str = f"{BASE_DIR}/lib/db/migrations"
    MIGRATION_DDL_VERSION_TABLE: str = "ddl_version"


class Settings(BaseSettings):
    """All Settings.

    All settings are nested here
    """

    api: APISettings
    app: AppSettings
    redis: RedisSettings
    db: DatabaseSettings
    openapi: OpenAPISettings
    server: ServerSettings
    log: LogSettings
    http_client: HTTPClientSettings
    worker: WorkerSettings


@lru_cache
def get_settings() -> Settings:
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
        server_settings.APP_LOC = "app.main:run_app"
        """Override Application host to allow connectivity from external IPs."""
        server_settings.HOST = "0.0.0.0"  # noqa: S104
        """Override Application host to allow connectivity from external IPs."""
        server_settings.RELOAD_DIRS = [str(BASE_DIR)]
        """Override Application reload dir."""
        app: AppSettings = app_settings
        api: APISettings = api_settings
        redis: RedisSettings = redis_settings
        db: DatabaseSettings = DatabaseSettings.parse_obj({})
        openapi: OpenAPISettings = openapi_settings
        server: ServerSettings = ServerSettings.parse_obj(server_settings.dict())
        log: LogSettings = log_settings
        worker: WorkerSettings = WorkerSettings.parse_obj(worker_settings.dict())
        http_client: HTTPClientSettings = http_client_settings
        settings = Settings(
            app=app,
            api=api,
            redis=redis,
            db=db,
            openapi=openapi,
            server=server,
            log=log,
            worker=worker,
            http_client=http_client,
        )
    except ValidationError as e:
        print("Could not load settings. %s", e)
        raise e from e
    return settings


_settings = get_settings()

app = _settings.app
api = _settings.api
db = _settings.db
openapi = _settings.openapi
redis = _settings.redis
server = _settings.server
log = _settings.log
worker = _settings.worker
http_client = _settings.http_client
