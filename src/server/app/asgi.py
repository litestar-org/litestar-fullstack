from starlite import Starlite, get

from app.lib import plugins


@get("/example")
def example_handler() -> dict:
    """Hello, world!"""
    return {"hello": "world"}


app = Starlite(route_handlers=[example_handler], on_app_init=[plugins.saqlalchemy])
