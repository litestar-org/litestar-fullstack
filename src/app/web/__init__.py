from starlite import Router

from app.web import routes

router = Router(
    path="",
    route_handlers=[
        routes.health_router,
        routes.access_router,
        routes.user_router,
        routes.collection_router,
        routes.frontend_router,
    ],
)


__all__ = ["routes", "router"]
