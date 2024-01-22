# pylint: disable=[invalid-name,import-outside-toplevel]
# SPDX-FileCopyrightText: 2023-present Cody Fincher <cody.fincher@gmail.com>
#
# SPDX-License-Identifier: MIT
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from litestar import Litestar
    from litestar.connection import Request


def create_app() -> Litestar:
    """Create ASGI application."""

    from uuid import UUID

    from advanced_alchemy.exceptions import RepositoryError
    from litestar import Litestar
    from litestar.config.app import ExperimentalFeatures
    from litestar.config.response_cache import ResponseCacheConfig
    from litestar.di import Provide
    from litestar.dto import DTOData
    from litestar.pagination import OffsetPagination
    from litestar.params import Dependency, Parameter
    from litestar.security.jwt import OAuth2Login
    from litestar.stores.redis import RedisStore
    from litestar.stores.registry import StoreRegistry

    from app.config import app as config
    from app.config import constants
    from app.config.base import get_settings
    from app.db.models import User
    from app.domain.accounts import signals as account_signals
    from app.domain.security import auth, provide_user
    from app.domain.teams import signals as team_signals
    from app.lib.dependencies import create_collection_dependencies
    from app.lib.exceptions import ApplicationError, exception_to_http_response
    from app.server import openapi, plugins, routers

    dependencies = {constants.USER_DEPENDENCY_KEY: Provide(provide_user)}
    dependencies.update(create_collection_dependencies())
    settings = get_settings()
    redis = settings.redis.get_client()

    def redis_store_factory(name: str) -> RedisStore:
        return RedisStore(redis, namespace=f"{settings.app.slug}:{name}")

    return Litestar(
        response_cache_config=ResponseCacheConfig(
            default_expiration=constants.CACHE_EXPIRATION,
            key_builder=_cache_key_builder,
        ),
        stores=StoreRegistry(default_factory=redis_store_factory),
        cors_config=config.cors,
        dependencies=dependencies,
        exception_handlers={
            ApplicationError: exception_to_http_response,
            RepositoryError: exception_to_http_response,
        },
        debug=settings.app.DEBUG,
        openapi_config=openapi.config,
        route_handlers=[*routers.routes],
        plugins=[
            plugins.structlog,
            plugins.alchemy,
            plugins.vite,
            plugins.saq,
            plugins.granian,
        ],
        on_shutdown=[redis.aclose],  # type: ignore[attr-defined]
        on_app_init=[auth.on_app_init],
        listeners=[account_signals.user_created_event_handler, team_signals.team_created_event_handler],
        experimental_features=[ExperimentalFeatures.DTO_CODEGEN],
        signature_types=[DTOData, OffsetPagination, OAuth2Login, User, UUID, Dependency, Parameter],
    )


def _cache_key_builder(request: Request) -> str:
    """App name prefixed cache key builder.

    Args:
        request (Request): Current request instance.

    Returns:
        str: App slug prefixed cache key.
    """
    from litestar.config.response_cache import default_cache_key_builder

    from app.config.base import get_settings

    settings = get_settings()

    return f"{settings.app.slug}:{default_cache_key_builder(request)}"


app = create_app()
