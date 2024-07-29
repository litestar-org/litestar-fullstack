from litestar import Controller, Request, get
from litestar.response import File
from litestar_vite.inertia import InertiaRedirect

from app.config import app as config


class WebController(Controller):
    """Web Controller."""

    include_in_schema = False

    @get(path="/", name="home", exclude_from_auth=True)
    async def home(self, request: Request) -> InertiaRedirect:
        """Serve site root."""
        if request.session.get("user_id", False):
            return InertiaRedirect(request, request.url_for("dashboard"))
        return InertiaRedirect(request, request.url_for("landing"))

    @get(component="landing", path="/landing/", name="landing", exclude_from_auth=True)
    async def landing(self) -> dict:
        """Serve site root."""
        return {}

    @get(component="dashboard", path="/dashboard/", name="dashboard")
    async def dashboard(self) -> dict:
        """Serve Dashboard Page."""
        return {}

    @get(component="about", path="/about/", name="about")
    async def about(self) -> dict:
        """Serve About Page."""
        return {}

    @get(component="legal/privacy-policy", path="/privacy-policy/", name="privacy-policy", exclude_from_auth=True)
    async def privacy_policy(self) -> dict:
        """Serve site root."""
        return {}

    @get(component="legal/terms-of-service", path="/terms-of-service/", name="terms-of-service", exclude_from_auth=True)
    async def legal(self) -> dict:
        """Serve site root."""
        return {}

    @get(path="/favicon.ico", name="favicon", exclude_from_auth=True, include_in_schema=False, sync_to_thread=False)
    def favicon(self) -> File:
        """Serve site root."""
        return File(path=f"{config.vite.public_dir}/favicon.ico")
