# pylint: disable=[invalid-name,import-outside-toplevel]
from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from litestar.config.response_cache import ResponseCacheConfig
from litestar.plugins import CLIPluginProtocol, InitPluginProtocol
from litestar.stores.redis import RedisStore
from litestar.stores.registry import StoreRegistry

if TYPE_CHECKING:
    from click import Group
    from litestar.config.app import AppConfig
    from redis.asyncio import Redis


T = TypeVar("T")


class ApplicationConfigurator(InitPluginProtocol, CLIPluginProtocol):
    """Application configuration plugin."""

    __slots__ = ("redis", "app_slug")
    redis: Redis
    app_slug: str

    def __init__(self) -> None:
        """Initialize ``ApplicationConfigurator``.

        Args:
            config: configure and start SAQ.
        """

    def on_cli_init(self, cli: Group) -> None:
        from app.cli.builder import build_management_cli_group
        from app.config import get_settings

        settings = get_settings()
        self.redis = settings.redis.get_client()
        self.app_slug = settings.app.slug
        cli.add_command(build_management_cli_group())

        return super().on_cli_init(cli)

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        """Configure application for use with SQLAlchemy.

        Args:
            app_config: The :class:`AppConfig <.config.app.AppConfig>` instance.
        """
        from litestar.contrib.jwt import OAuth2Login, Token
        from litestar.pagination import OffsetPagination
        from uuid_utils import UUID

        from app.config import constants, get_settings
        from app.db.models import User
        from app.lib.repository import SQLAlchemyAsyncSlugRepository

        settings = get_settings()
        self.redis = settings.redis.get_client()
        self.app_slug = settings.app.slug
        app_config.response_cache_config = ResponseCacheConfig(default_expiration=constants.CACHE_EXPIRATION)
        app_config.stores = StoreRegistry(default_factory=self.redis_store_factory)
        app_config.on_shutdown.append(self.redis.aclose)  # type: ignore[attr-defined]
        app_config.signature_namespace.update(
            {
                "UUID": UUID,
                "User": User,
                "Token": Token,
                "OAuth2Login": OAuth2Login,
                "OffsetPagination": OffsetPagination,
                "SQLAlchemyAsyncSlugRepository": SQLAlchemyAsyncSlugRepository,
            },
        )
        return app_config

    def redis_store_factory(self, name: str) -> RedisStore:
        return RedisStore(self.redis, namespace=f"{self.app_slug}:{name}")