from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from starlite import CompressionConfig, Starlite

from pyspa import routes
from pyspa.config import settings
from pyspa.config.logging import log_config
from pyspa.core import exceptions, openapi, response

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
