from litestar import Controller, get
from litestar.status_codes import HTTP_200_OK

from app.lib.schema import Message


class WebController(Controller):
    """Web Controller."""

    include_in_schema = False
    opt = {"exclude_from_auth": True}

    @get(
        component="home",
        path="/",
        operation_id="WebIndex",
        name="frontend:index",
        status_code=HTTP_200_OK,
    )
    async def index(self, path: str | None = None) -> Message:
        """Serve site root."""
        return Message("Welcome back.")
