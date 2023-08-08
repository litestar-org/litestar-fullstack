# pylint: disable=[invalid-name,import-outside-toplevel]
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from litestar import Litestar


__all__ = ["create_app"]


def create_app() -> Litestar:
    """Create ASGI application."""

    from asyncpg.pgproto import pgproto
    from litestar import Litestar
    from litestar.di import Provide
    from litestar.stores.registry import StoreRegistry
    from pydantic import SecretStr

    from app import domain
    from app.domain.security import provide_user
    from app.lib import (
        cache,
        constants,
        cors,
        exceptions,
        repository,
        settings,
        static_files,
    )
    from app.lib.dependencies import create_collection_dependencies

    dependencies = {constants.USER_DEPENDENCY_KEY: Provide(provide_user)}
    dependencies.update(create_collection_dependencies())
    return Litestar(
        response_cache_config=cache.config,
        stores=StoreRegistry(default_factory=cache.redis_store_factory),
        cors_config=cors.config,
        dependencies=dependencies,
        exception_handlers={
            exceptions.ApplicationError: exceptions.exception_to_http_response,  # type: ignore[dict-item]
        },
        debug=settings.app.DEBUG,
        openapi_config=domain.openapi.config,
        type_encoders={pgproto.UUID: str, SecretStr: str},
        route_handlers=[*domain.routes],
        plugins=domain.plugins.enabled_plugins,
        on_shutdown=[cache.redis.close],
        on_app_init=[domain.security.auth.on_app_init, repository.on_app_init],
        static_files_config=static_files.config,
        signature_namespace=domain.signature_namespace,
    )
