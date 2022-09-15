"""
All configuration is via environment variables.

Take not of the environment variable prefixes required for each settings class, except
[`AppSettings`][starlite_lib.config.AppSettings].
"""
import logging
import sys
from datetime import datetime
from enum import Enum, EnumMeta
from functools import lru_cache
from typing import Any, Literal, Optional, Union, cast
from uuid import NAMESPACE_DNS, uuid3

from pydantic import BaseSettings as _BaseSettings
from pydantic import SecretBytes, SecretStr, ValidationError, validator

from pyspa.config.paths import BASE_DIR
from pyspa.utils.serializers import convert_datetime_to_gmt, deserialize_object, serialize_object
from pyspa.utils.text import slugify
from pyspa.version import __version__

__all__ = [
    "BASE_DIR",
    "BaseSettings",
    "EnvironmentSettings",
    "Settings",
    "settings",
]

logger = logging.getLogger()


class BaseSettings(_BaseSettings):
    """Base Settings"""

    class Config:
        """Base Settings Config"""

        json_loads = deserialize_object
        json_dumps = serialize_object
        case_sensitive = True
        json_encoders = {
            datetime: convert_datetime_to_gmt,
            SecretStr: lambda secret: secret.get_secret_value() if secret else None,
            SecretBytes: lambda secret: secret.get_secret_value() if secret else None,
            Enum: lambda enum: enum.value if enum else None,
            EnumMeta: None,
        }
        validate_assignment = True
        orm_mode = True
        use_enum_values = True


class EnvironmentSettings(BaseSettings):
    """Settings That can be controlled with environment variables"""

    class Config:
        """Environment Settings Config"""

        env_file = ".env"
        env_file_encoding = "utf-8"


class AppSettings(EnvironmentSettings):
    class Config:
        case_sensitive = True

    NAME: str = "optimus-prime"
    SECRET_KEY: SecretStr
    BUILD_NUMBER: str = __version__
    DEBUG: bool = False
    DEFAULT_PAGINATION_LIMIT: int = 10
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"
    DEV_MODE: bool = False
    JWT_ENCRYPTION_ALGORITHM: str = "HS256"
    USER_REGISTRATION_ENABLED: bool = True
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day expiration
    REFRESH_TOKEN_COOKIE_NAME: str = "refresh-token"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 5
    ACCESS_TOKEN_COOKIE_NAME: str = "access-token"
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 24
    INVITE_TOKEN_EXPIRE_HOURS: int = 24
    USER_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    BACKEND_CORS_ORIGINS: list[str] = []
    CSRF_COOKIE_NAME: str = "csrftoken"
    CSRF_COOKIE_SECURE: bool = True

    @property
    def slug(self) -> str:
        """
        A slugified name.

        Returns
        -------
        str
            `self.NAME`, all lowercase and hyphens instead of spaces.
        """
        return slugify(self.NAME)

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(
        cls,
        value: Union[str, list[str]],
    ) -> Union[list[str], str]:
        """Parses a list of origins"""

        if isinstance(value, list):
            return value
        if isinstance(value, str) and not value.startswith("["):
            return [host.strip() for host in value.split(",")]
        elif isinstance(value, str) and value.startswith("[") and value.endswith("]"):
            return list(value)
        raise ValueError(value)


# noinspection PyUnresolvedReferences
class OpenAPISettings(BaseSettings):
    """
    Configures OpenAPI for the application.

    Prefix all environment variables with `OPENAPI_`, e.g., `OPENAPI_TITLE`.

    Attributes
    ----------
    TITLE : str
        OpenAPI document title.
    VERSION : str
        OpenAPI document version.
    CONTACT_NAME : str
        OpenAPI document contact name.
    CONTACT_EMAIL : str
        OpenAPI document contact email.
    """

    TITLE: str | None
    VERSION: str = "v1"
    CONTACT_NAME: str = "Admin"
    CONTACT_EMAIL: str = "admin@localhost"


# noinspection PyUnresolvedReferences
class DatabaseSettings(EnvironmentSettings):
    """
    Configures the database for the application.

    Prefix all environment variables with `DB_`, e.g., `DB_URL`.

    Attributes
    ----------
    ECHO : bool
        Enables SQLAlchemy engine logs.
    URL : PostgresDsn
        URL for database connection.
    """

    class Config:
        env_prefix = "DB_"
        case_sensitive = True

    ECHO: bool = False
    ECHO_POOL: bool | Literal["debug"] = False
    POOL_DISABLE: bool = False
    POOL_MAX_OVERFLOW: int = 20
    POOL_SIZE: int = 10
    POOL_TIMEOUT: int = 30
    POOL_RECYCLE: int = 300
    POOL_PRE_PING: bool = True
    URL: str
    MIGRATION_CONFIG: str = f"{BASE_DIR}/config/alembic.ini"
    MIGRATION_PATH: str = f"{BASE_DIR}/db/migrations"
    MIGRATION_DDL_VERSION_TABLE: str = "ddl_version"


# noinspection PyUnresolvedReferences
class CacheSettings(EnvironmentSettings):
    """
    Cache settings for the application.

    Prefix all environment variables with `CACHE_`, e.g., `CACHE_URL`.

    Attributes
    ----------
    URL : AnyUrl
        A redis connection URL.
    """

    class Config:
        env_prefix = "CACHE_"
        case_sensitive = True

    URL: str
    EXPIRATION: int = 60


class ServerSettings(EnvironmentSettings):
    """Uvicorn Specific Configuration"""

    class Config:
        env_prefix = "SERVER_"

    ASGI_APP: str = "pyspa.asgi:app"
    HOST: str = "0.0.0.0"  # nosec
    PORT: int = 8000
    HTTP_WORKERS: int = 1
    BACKGROUND_WORKERS: int = 1
    RELOAD: bool = False
    UVICORN_LOG_LEVEL: str = "WARNING"
    GUNICORN_LOG_LEVEL: str = "WARNING"


class Settings(BaseSettings):
    """
    Settings

    All settings are nested here
    """

    app: AppSettings
    cache: CacheSettings
    db: DatabaseSettings
    openapi: OpenAPISettings
    server: ServerSettings

    installation_id: str | None = None

    @validator("installation_id", pre=True, always=True)
    def generate_installation_id(
        cls,
        value: Optional[str],
        values: dict[str, Any],
    ) -> str:
        if isinstance(value, str):
            return slugify(value)
        db = cast("DatabaseSettings", values.get("db"))
        return str(uuid3(NAMESPACE_DNS, db.URL))


@lru_cache
def get_settings(env: str = "production") -> "Settings":
    """Load Settings file

    Returns:
        Settings: _description_
    """
    try:
        app: AppSettings = AppSettings()
        cache: CacheSettings = CacheSettings()
        db: DatabaseSettings = DatabaseSettings()
        openapi: OpenAPISettings = OpenAPISettings()
        server: ServerSettings = ServerSettings()

        settings = Settings(app=app, cache=cache, db=db, openapi=openapi, server=server)
    except ValidationError as e:
        logger.fatal(f"Could not load settings. {e}")
        sys.exit(1)
    return settings


settings = get_settings()
