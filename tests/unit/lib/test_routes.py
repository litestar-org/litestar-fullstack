from __future__ import annotations

import json
from typing import TYPE_CHECKING, TypedDict

from litestar.app import DEFAULT_OPENAPI_CONFIG
from litestar.cli._utils import (
    remove_default_schema_routes,
    remove_routes_with_patterns,
)
from litestar.routes import ASGIRoute, WebSocketRoute

from app.asgi import app

if TYPE_CHECKING:
    from litestar import Litestar


class Routes(TypedDict):
    routes: dict[str, str]


EXCLUDED_METHODS = {"HEAD", "OPTIONS", "TRACE"}


def generate_js_routes(
    app: Litestar,
    exclude: tuple[str, ...] | None = None,
    schema: bool = False,
) -> Routes:
    sorted_routes = sorted(app.routes, key=lambda r: r.path)
    if not schema:
        openapi_config = app.openapi_config or DEFAULT_OPENAPI_CONFIG
        sorted_routes = remove_default_schema_routes(sorted_routes, openapi_config)
    if exclude is not None:
        sorted_routes = remove_routes_with_patterns(sorted_routes, exclude)
    route_list: dict[str, str] = {}
    for route in sorted_routes:
        if isinstance(route, (ASGIRoute, WebSocketRoute)):
            route_name = route.route_handler.name or route.route_handler.handler_name
            if len(route.methods.difference(EXCLUDED_METHODS)) > 0:
                route_list[route_name] = route.path
        else:
            for handler in route.route_handlers:
                route_name = handler.name or handler.handler_name
                if handler.http_methods.isdisjoint(EXCLUDED_METHODS):
                    route_list[route_name] = route.path

    return {"routes": route_list}


def test_route_export() -> None:
    test_1 = {"POST", "OPTIONS"}
    test_2 = {"POST", "OPTIONS", "HEAD"}
    test_3 = {"HEAD"}
    test_4 = {"GET"}
    _len_1 = len(test_1.difference(EXCLUDED_METHODS))
    _len_2 = len(test_2.difference(EXCLUDED_METHODS))
    _len_3 = len(test_3.difference(EXCLUDED_METHODS))
    _len_4 = test_4.isdisjoint(EXCLUDED_METHODS)
    routes = generate_js_routes(app=app)
    json_response = json.dumps(routes)
    assert json_response
    assert routes is not None
