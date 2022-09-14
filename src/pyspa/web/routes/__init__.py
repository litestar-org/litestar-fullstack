from starlite import Router

from pyspa.web.routes import collection, health

__all__ = ["collection_router", "health_router", "organization_router", "access_router", "user_router"]

collection_router = Router(
    path="",
    route_handlers=[collection.handle_collection_upload],
)
health_router = Router(
    path="",
    route_handlers=[health.health_check],
)
organization_router = Router(
    path="",
    route_handlers=[],
)
access_router = Router(
    path="",
    route_handlers=[],
)
user_router = Router(
    path="",
    route_handlers=[],
)
