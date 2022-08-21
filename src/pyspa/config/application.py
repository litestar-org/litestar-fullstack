import datetime
from enum import Enum, EnumMeta
from functools import lru_cache

from pydantic import AnyUrl
from pydantic import BaseSettings as _BaseSettings
from pydantic import PostgresDsn, SecretBytes, SecretStr

from pyspa.__version__ import __version__


def encode_datetime_object(dt: datetime.datetime) -> str:
    """Handles datetime serialization for nested timestamps in models/dataclasses"""
    return dt.replace(tzinfo=datetime.timezone.utc).isoformat().replace("+00:00", "Z")


class BaseSettings(_BaseSettings):
    class Config:
        case_sensitive = True
        json_encoders = {
            datetime.datetime: encode_datetime_object,
            SecretStr: lambda secret: secret.get_secret_value() if secret else None,
            SecretBytes: lambda secret: secret.get_secret_value() if secret else None,
            Enum: lambda enum: enum.value if enum else None,
            EnumMeta: None,
        }
        validate_assignment = True
        case_sensitive = False
        orm_mode = True
        use_enum_values = True
        env_file = ".env"
        env_file_encoding = "utf-8"


class ApplicationSettings(BaseSettings):
    class Config:
        env_prefix = "PYSPA_"

    BUILD_NUMBER: str = str(__version__)
    DEBUG: bool = False
    DEFAULT_PAGINATION_LIMIT: int = 10
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"
    DEV_MODE: bool = False
    NAME: str = "pyspa"


class CacheSettings(BaseSettings):
    class Config:
        env_prefix = "PYSPA_REDIS_"

    EXPIRATION: int = 60  # 60 seconds
    URL: AnyUrl


class DatabaseSettings(BaseSettings):
    """Database Configuration"""

    class Config:
        env_prefix = "PYSPA_POSTGRES_"

    ECHO: bool = False
    URL: PostgresDsn


class GunicornSettings(BaseSettings):
    """Gunicorn settings"""

    class Config:
        env_prefix = "PYSPA_GUNICORN_"

    ACCESS_LOG: str
    ERROR_LOG: str
    HOST: str = "0.0.0.0"
    KEEPALIVE: int = 120
    LOG_LEVEL: str = "INFO"
    PORT: int = 8080
    RELOAD: bool = False
    THREADS: int
    TIMEOUT: int = 120
    WORKERS: int
    WORKER_CLASS: str
    PRELOAD: bool = True


# Constants
class ApiPaths:
    HEALTH = "/health"


class Settings(BaseSettings):
    """Main Setting Class"""

    app: ApplicationSettings = ApplicationSettings()
    db: DatabaseSettings = DatabaseSettings()
    cache: CacheSettings = CacheSettings()
    gunicorn: GunicornSettings = GunicornSettings()
    api_paths: ApiPaths = ApiPaths()


@lru_cache(maxsize=1)
def get_app_settings() -> Settings:
    """
    Cache app settings

    This function returns a configured instance of settings.

    LRU Cache decorator has been used to limit the number of instances to 1.
    This effectively turns this into a singleton class.

    Maybe there are better approaches for this?
    """
    return Settings()


settings = get_app_settings()
