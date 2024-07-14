from litestar import Controller, get


class WebController(Controller):
    """Web Controller."""

    include_in_schema = False

    @get(component="home", path="/", name="home", exclude_from_auth=True)
    async def home(self) -> dict:
        """Serve site root."""
        return {}

    @get(component="dashboard", path="/dashboard", name="dashboard")
    async def dashboard(self) -> dict:
        """Serve Dashboard Page."""
        return {}

    @get(component="about", path="/about", name="about")
    async def about(self) -> dict:
        """Serve About Page."""
        return {}

    @get(component="legal", path="/legal", name="legal")
    async def legal(self) -> dict:
        """Serve site root."""
        return {}
