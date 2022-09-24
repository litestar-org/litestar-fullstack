from starlite import Router

from app.api.routes import collection, health, user

__all__ = ["collection_router", "health_router", "access_router", "user_router"]

collection_router = Router(
    path="",
    route_handlers=[collection.CollectionController],
)
health_router = Router(
    path="",
    route_handlers=[health.health_check],
)
access_router = Router(
    path="",
    route_handlers=[user.login, user.signup],
)
user_router = Router(
    path="",
    route_handlers=[],
)
