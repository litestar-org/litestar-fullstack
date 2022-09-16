from starlite import Router

from pyspa.api import routes
from pyspa.config.paths import urls

router = Router(
    path=urls.API_BASE,
    route_handlers=[
        routes.health_router,
        routes.access_router,
        routes.user_router,
        routes.collection_router,
    ],
)


__all__ = ["routes", "router"]
