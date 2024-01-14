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

    from advanced_alchemy.exceptions import RepositoryError
    from litestar import Litestar
    from litestar.config.app import ExperimentalFeatures
    from litestar.config.response_cache import ResponseCacheConfig
    from litestar.di import Provide
    from litestar.stores.redis import RedisStore
    from litestar.stores.registry import StoreRegistry

    from app import domain
    from app.config import constants, settings
    from app.domain import config
    from app.domain.security import provide_user
    from app.lib.dependencies import create_collection_dependencies
    from app.lib.exceptions import ApplicationError, exception_to_http_response

    dependencies = {constants.USER_DEPENDENCY_KEY: Provide(provide_user)}
    dependencies.update(create_collection_dependencies())

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
        openapi_config=domain.openapi.config,
        route_handlers=[*domain.routes],
        plugins=[
            domain.plugins.structlog,
            domain.plugins.alchemy,
            domain.plugins.vite,
            domain.plugins.saq,
            domain.plugins.pydantic,
        ],
        on_shutdown=[redis.aclose],  # type: ignore[attr-defined]
        on_app_init=[domain.security.auth.on_app_init],
        listeners=[domain.accounts.signals.user_created_event_handler],
        signature_namespace=domain.signature_namespace,
        experimental_features=[ExperimentalFeatures.DTO_CODEGEN],
    )


def _cache_key_builder(request: Request) -> str:
    """App name prefixed cache key builder.

    Args:
        request (Request): Current request instance.

    Returns:
        str: App slug prefixed cache key.
    """
    from litestar.config.response_cache import default_cache_key_builder

    from app.config import settings

    return f"{settings.app.slug}:{default_cache_key_builder(request)}"


app = create_app()
