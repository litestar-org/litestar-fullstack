from starlite import Controller, Template, get
from starlite.status_codes import HTTP_200_OK

from app.domain import urls


class WebController(Controller):
    """Web Controller."""

    opt = {"exclude_from_auth": True}

    @get(
        [urls.INDEX, urls.SITE_ROOT],
        operation_id="WebIndex",
        name="frontend:index",
        status_code=HTTP_200_OK,
        include_in_schema=False,
        opt={"exclude_from_auth": True},
    )
    async def index(self) -> Template:
        """Serve site root."""
        return Template(name="site/index.html.j2")
