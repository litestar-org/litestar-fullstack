from litestar import Controller, get
from litestar.response import Template
from litestar.status_codes import HTTP_200_OK

from app.config import constants


class WebController(Controller):
    """Web Controller."""

    include_in_schema = False
    opt = {"exclude_from_auth": True}

    @get(
        path=[constants.SITE_INDEX, f"{constants.SITE_INDEX}/{{path:path}}"],
        operation_id="WebIndex",
        name="frontend:index",
        status_code=HTTP_200_OK,
    )
    async def index(self, path: str | None = None) -> Template:
        """Serve site root."""
        return Template(template_name="site/index.html.j2")
