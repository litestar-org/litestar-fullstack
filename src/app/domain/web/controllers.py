from litestar import Controller, Request, get
from litestar_vite.inertia import InertiaRedirect


class WebController(Controller):
    """Web Controller."""

    include_in_schema = False

    @get(path="/", name="home", exclude_from_auth=True)
    async def home(self, request: Request) -> InertiaRedirect:
        """Serve site root."""
        if request.session.get("user_id", False):
            return InertiaRedirect(request, request.url_for("dashboard"))
        return InertiaRedirect(request, request.url_for("landing"))

    @get(component="home", path="/landing", name="landing", exclude_from_auth=True)
    async def landing(self) -> dict:
        """Serve site root."""
        return {}

    @get(component="dashboard", path="/dashboard", name="dashboard")
    async def dashboard(self) -> dict:
        """Serve Dashboard Page."""
        return {}

    @get(component="about", path="/about", name="about", exclude_from_auth=True)
    async def about(self) -> dict:
        """Serve About Page."""
        return {}

    @get(component="legal/privacy-policy", path="/privacy-policy", name="privacy-policy", exclude_from_auth=True)
    async def privacy_policy(self) -> dict:
        """Serve site root."""
        return {}

    @get(component="legal/terms-of-service", path="/terms-of-service", name="terms-of-service", exclude_from_auth=True)
    async def legal(self) -> dict:
        """Serve site root."""
        return {}
