from functools import cache

from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from advanced_alchemy.types.file_object import storages
from advanced_alchemy.types.file_object.backends.obstore import ObstoreBackend
from litestar.plugins.problem_details import ProblemDetailsPlugin
from litestar.plugins.structlog import StructlogPlugin
from litestar_email import EmailPlugin
from litestar_granian import GranianPlugin
from litestar_saq import SAQPlugin
from litestar_vite import VitePlugin
from obstore.store import S3Store

from app import config
from app.lib.settings import StorageSettings
from app.utils.domain import DomainPlugin
from app.utils.oauth import OAuth2ProviderPlugin

structlog = StructlogPlugin(config=config.log)
vite = VitePlugin(config=config.vite)
alchemy = SQLAlchemyPlugin(config=config.alchemy)
granian = GranianPlugin()
problem_details = ProblemDetailsPlugin(config=config.problem_details)
oauth2_provider = OAuth2ProviderPlugin()
email = EmailPlugin(config=config.email)
domain = DomainPlugin()


def register_storage_backend() -> None:
    """Register the S3-compatible storage backend for file objects.

    Idempotent: if a backend is already registered under the configured key
    (e.g. an in-memory store installed by the test suite) the registration is
    skipped so test overrides survive application init.
    """
    import structlog as _structlog

    if storages.is_registered(StorageSettings.BACKEND_KEY):
        return

    logger = _structlog.get_logger()
    storage_settings = config.storage
    s3_store = S3Store(
        bucket=storage_settings.S3_BUCKET,
        config={
            "access_key_id": storage_settings.S3_ACCESS_KEY,
            "secret_access_key": storage_settings.S3_SECRET_KEY,
            "endpoint": storage_settings.S3_ENDPOINT,
            "region": storage_settings.S3_REGION,
            "allow_http": storage_settings.S3_ALLOW_HTTP,
        },
    )
    backend = ObstoreBackend(key=StorageSettings.BACKEND_KEY, fs=s3_store)
    storages.register_backend(backend)
    logger.info(
        "Registered S3 storage backend",
        bucket=storage_settings.S3_BUCKET,
        endpoint=storage_settings.S3_ENDPOINT,
    )


@cache
def get_saq_plugin() -> SAQPlugin:
    """Get SAQ plugin lazily to avoid Redis connection during build."""
    return SAQPlugin(config=config.get_saq_config())
