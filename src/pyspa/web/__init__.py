from starlite import Router

from pyspa.config.paths import urls
from pyspa.web import routes

router = Router(
    path=urls.API_BASE,
    route_handlers=[
        routes.health_router,
        routes.user_router,
        routes.collection_router,
        routes.organization_router,
    ],
)


__all__ = ["routes"]
