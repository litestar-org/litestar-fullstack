from app.web.routes import collection, frontend, health, user
from starlite import Router

__all__ = ["collection_router", "health_router", "access_router", "user_router", "frontend_router"]

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
frontend_router = Router(
    path="",
    route_handlers=[frontend.site_index, frontend.authenticated_test],
)
