from starlite import Starlite
from starlite.plugins.sql_alchemy import SQLAlchemyPlugin
from starlite.status_codes import HTTP_500_INTERNAL_SERVER_ERROR

from app import web
from app.config import log_config, settings
from app.core import cache, client, compression, cors, db, exceptions, openapi, response, security, static_files

__all__ = ["app"]


app = Starlite(
    debug=settings.app.DEBUG,
    exception_handlers={HTTP_500_INTERNAL_SERVER_ERROR: exceptions.logging_exception_handler},
    on_shutdown=[client.on_shutdown, cache.on_shutdown],
    logging_config=log_config,
    openapi_config=openapi.config,
    compression_config=compression.config,
    cors_config=cors.config,
    route_handlers=[web.router],
    cache_config=cache.config,
    response_class=response.Response,
    middleware=[security.auth.middleware],
    plugins=[SQLAlchemyPlugin(config=db.config)],
    static_files_config=static_files.config,
    allowed_hosts=settings.app.BACKEND_CORS_ORIGINS,
)
