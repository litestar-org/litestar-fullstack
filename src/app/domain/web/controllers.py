from litestar import Controller, get

from app.lib.schema import Message


class WebController(Controller):
    """Web Controller."""

    include_in_schema = False
    opt = {"exclude_from_auth": True}

    @get(
        component="home",
        path="/",
        name="home",
    )
    async def home(self, path: str | None = None) -> Message:
        """Serve site root."""
        return Message("Welcome back.")

    @get(
        component="dashboard",
        path="/dashboard",
        name="dashboard",
    )
    async def dashboard(self, path: str | None = None) -> Message:
        """Serve Dashboard Page."""
        return Message("Welcome back.")

    @get(
        component="about",
        path="/about",
        name="about",
    )
    async def about(self, path: str | None = None) -> Message:
        """Serve About Page."""
        return Message("Welcome back.")

    @get(
        component="legal",
        path="/legal",
        name="legal",
    )
    async def legal(self, path: str | None = None) -> Message:
        """Serve site root."""
        return Message("Welcome back.")
