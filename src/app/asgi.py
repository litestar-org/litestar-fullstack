# pylint: disable=[invalid-name,import-outside-toplevel]
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from starlite import Starlite


__all__ = ["create_app"]


def create_app() -> Starlite:
    """Create ASGI application."""
    from datetime import datetime
    from uuid import UUID

    from asyncpg.pgproto import pgproto
    from pydantic import BaseModel, EmailStr, SecretStr
    from sqlalchemy.ext.asyncio import AsyncSession
    from starlite import Starlite
    from starlite.connection import ASGIConnection, Request
    from starlite.contrib.jwt import OAuth2Login
    from starlite.contrib.repository.filters import (
        BeforeAfter,
        CollectionFilter,
        LimitOffset,
    )
    from starlite.di import Provide
    from starlite.pagination import OffsetPagination
    from starlite.stores.registry import StoreRegistry

    from app import domain
    from app.domain.accounts.models import User
    from app.domain.security import provide_user
    from app.domain.web.vite import template_config
    from app.lib import cache, compression, constants, cors, db, exceptions, log, settings, static_files
    from app.lib.dependencies import FilterTypes, create_collection_dependencies

    dependencies = {constants.USER_DEPENDENCY_KEY: Provide(provide_user)}
    dependencies.update(create_collection_dependencies())

    def _base_model_encoder(value: BaseModel) -> dict[str, Any]:
        return value.dict(by_alias=True)

    return Starlite(
        response_cache_config=cache.config,
        stores=StoreRegistry(default_factory=cache.redis_store_factory),
        compression_config=compression.config,
        cors_config=cors.config,
        dependencies=dependencies,
        exception_handlers={
            exceptions.ApplicationError: exceptions.exception_to_http_response,
        },
        debug=settings.app.DEBUG,
        before_send=[log.controller.BeforeSendHandler()],
        middleware=[log.controller.middleware_factory],
        logging_config=log.config,
        openapi_config=domain.openapi.config,
        type_encoders={pgproto.UUID: str, BaseModel: _base_model_encoder, SecretStr: str},
        route_handlers=[*domain.routes],
        plugins=[db.plugin],
        on_shutdown=[cache.redis.close],
        on_startup=[lambda: log.configure(log.default_processors)],  # type: ignore[arg-type]
        on_app_init=[domain.security.auth.on_app_init],
        static_files_config=static_files.config,
        template_config=template_config,  # type: ignore[arg-type]
        signature_namespace={
            "AsyncSession": AsyncSession,
            "FilterTypes": FilterTypes,
            "BeforeAfter": BeforeAfter,
            "CollectionFilter": CollectionFilter,
            "LimitOffset": LimitOffset,
            "UUID": UUID,
            "EmailStr": EmailStr,
            "datetime": datetime,
            "User": User,
            "ASGIConnection": ASGIConnection,
            "Request": Request,
            "OAuth2Login": OAuth2Login,
            "OffsetPagination": OffsetPagination,
        },
    )
