from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from starlite import Provide, Starlite

from app import api, db, middleware
from app.config import log_config, settings
from app.core import cache, client, compression, cors, exceptions, openapi, response, security, static_files

__all__ = ["app"]


app = Starlite(
    debug=settings.app.DEBUG,
    exception_handlers={HTTP_500_INTERNAL_SERVER_ERROR: exceptions.logging_exception_handler},
    on_shutdown=[db.on_shutdown, client.on_shutdown, cache.on_shutdown],
    on_startup=[log_config.configure],
    openapi_config=openapi.config,
    compression_config=compression.config,
    cors_config=cors.config,
    route_handlers=[api.router],
    cache_config=cache.config,
    response_class=response.Response,
    middleware=[security.auth.middleware, middleware.DatabaseSessionMiddleware],
    dependencies={"db": Provide(db.db_session)},
    static_files_config=static_files.config,
    allowed_hosts=settings.app.BACKEND_CORS_ORIGINS,
)
