from opdba import routes
from opdba.config import settings
from opdba.config.logging import log_config
from opdba.core import exceptions, openapi, response
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from starlite import CompressionConfig, Starlite

app = Starlite(
    debug=settings.app.DEBUG,
    exception_handlers={
        HTTP_500_INTERNAL_SERVER_ERROR: exceptions.logging_exception_handler
    },
    compression_config=CompressionConfig(backend="brotli"),
    middleware=[],
    on_shutdown=[],
    on_startup=[log_config.configure],
    openapi_config=openapi.config,
    response_class=response.Response,
    route_handlers=[routes.health_check],
)
