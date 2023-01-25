from starlite import get


@get("/example")
def example_handler() -> dict:
    """Hello, world!"""
    return {"hello": "world"}
