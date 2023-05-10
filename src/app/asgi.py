# pylint: disable=[invalid-name,import-outside-toplevel]
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from litestar import Litestar
    from pydantic import BaseModel


__all__ = ["create_app"]


def create_app() -> Litestar:
    """Create ASGI application."""
    from datetime import datetime
    from uuid import UUID

    from asyncpg.pgproto import pgproto
    from litestar import Litestar
    from litestar.connection import Request
    from litestar.contrib.jwt import OAuth2Login
    from litestar.di import Provide
    from litestar.pagination import OffsetPagination
    from litestar.serialization import DEFAULT_TYPE_ENCODERS
    from litestar.stores.registry import StoreRegistry
    from pydantic import UUID4, BaseModel, EmailStr, SecretStr
    from saq.types import QueueInfo
    from sqlalchemy import PoolProxiedConnection
    from sqlalchemy.engine.interfaces import DBAPIConnection
    from sqlalchemy.ext.asyncio import AsyncSession

    from app import domain
    from app.domain.accounts.models import User
    from app.domain.accounts.services import UserService
    from app.domain.security import provide_user
    from app.domain.teams.services import TeamInvitationService, TeamMemberService, TeamService
    from app.domain.web.vite import template_config
    from app.lib import (
        cache,
        constants,
        cors,
        db,
        exceptions,
        log,
        repository,
        settings,
        static_files,
        worker,
    )
    from app.lib.db.base import SQLAlchemyAiosqlQueryManager
    from app.lib.dependencies import (
        FilterTypes,
        create_collection_dependencies,
    )
    from app.lib.repository import SQLAlchemyAsyncRepository, SQLAlchemyAsyncSlugRepository
    from app.lib.service.generic import Service
    from app.lib.service.sqlalchemy import SQLAlchemyAsyncRepositoryService

    dependencies = {constants.USER_DEPENDENCY_KEY: Provide(provide_user)}
    dependencies.update(create_collection_dependencies())

    return Litestar(
        response_cache_config=cache.config,
        stores=StoreRegistry(default_factory=cache.redis_store_factory),
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
        type_encoders={**DEFAULT_TYPE_ENCODERS, pgproto.UUID: str, BaseModel: _base_model_encoder, SecretStr: str},
        route_handlers=[*domain.routes],
        plugins=[db.plugin],
        on_shutdown=[cache.redis.close],
        on_startup=[lambda: log.configure(log.default_processors)],  # type: ignore[arg-type]
        on_app_init=[domain.security.auth.on_app_init, repository.on_app_init],
        static_files_config=static_files.config,
        template_config=template_config,  # type: ignore[arg-type]
        signature_namespace={
            "AsyncSession": AsyncSession,
            "Service": Service,
            "FilterTypes": FilterTypes,
            "UUID4": UUID4,
            "UUID": UUID,
            "EmailStr": EmailStr,
            "datetime": datetime,
            "User": User,
            "Request": Request,
            "OAuth2Login": OAuth2Login,
            "OffsetPagination": OffsetPagination,
            "UserService": UserService,
            "TeamService": TeamService,
            "TeamInvitationService": TeamInvitationService,
            "TeamMemberService": TeamMemberService,
            "SQLAlchemyAsyncRepositoryService": SQLAlchemyAsyncRepositoryService,
            "SQLAlchemyAsyncRepository": SQLAlchemyAsyncRepository,
            "SQLAlchemyAsyncSlugRepository": SQLAlchemyAsyncSlugRepository,
            "PoolProxiedConnection": PoolProxiedConnection,
            "SQLAlchemyAiosqlQueryManager": SQLAlchemyAiosqlQueryManager,
            "DBAPIConnection": DBAPIConnection,
            "Queue": worker.Queue,
            "QueueInfo": QueueInfo,
            "Job": worker.Job,
        },
    )


def _base_model_encoder(value: BaseModel) -> dict[str, Any]:
    return value.dict(by_alias=True)
