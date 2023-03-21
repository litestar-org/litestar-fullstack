# pylint: disable=[invalid-name,import-outside-toplevel]
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from starlite import Starlite


__all__ = ["run_app"]


def run_app() -> Starlite:
    """Create ASGI application."""
    from pydantic import BaseModel, SecretStr
    from starlite import Starlite
    from starlite.di import Provide

    from app import domain
    from app.domain.security import provide_user
    from app.domain.web.vite import template_config
    from app.lib import cache, compression, constants, cors, db, exceptions, log, settings, static_files
    from app.lib.dependencies import create_collection_dependencies

    dependencies = {constants.USER_DEPENDENCY_KEY: Provide(provide_user)}
    dependencies.update(create_collection_dependencies())

    def _base_model_encoder(value: BaseModel) -> dict[str, Any]:
        return value.dict(by_alias=True)

    return Starlite(
        cache_config=cache.config,
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
        type_encoders={BaseModel: _base_model_encoder, SecretStr: str},
        route_handlers=[*domain.routes],
        plugins=[db.plugin],
        on_shutdown=[cache.redis.close],
        on_startup=[lambda: log.configure(log.default_processors)],  # type: ignore[arg-type]
        on_app_init=[domain.security.auth.on_app_init],
        static_files_config=static_files.config,
        template_config=template_config,  # type: ignore[arg-type]
    )
