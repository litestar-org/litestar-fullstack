from __future__ import annotations

import anyio
from litestar import Controller, MediaType, Response, get
from litestar.exceptions import NotFoundException
from litestar.status_codes import HTTP_200_OK

from app.lib.settings import STATIC_DIR


class WebController(Controller):
    """Web Controller."""

    opt = {"exclude_from_auth": True}
    include_in_schema = False

    @get(["/", "/{path:path}"], operation_id="WebIndex", status_code=HTTP_200_OK)
    async def index(self) -> Response[str]:
        """Serve site root.

        Raises:
            NotFoundException: raised when index file is missing.

        Returns:
            Response: An HTTP Response with the Index contents embedded
        """
        exists = await anyio.Path(STATIC_DIR / "index.html").exists()
        if exists:
            async with await anyio.open_file(anyio.Path(STATIC_DIR / "index.html")) as file:
                content = await file.read()
                return Response(content=content, status_code=HTTP_200_OK, media_type=MediaType.HTML)
        msg = "Site index was not found"
        raise NotFoundException(msg)
