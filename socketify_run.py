from __future__ import annotations

from typing import TYPE_CHECKING

from socketify import ASGI

from app.asgi import create_app

if TYPE_CHECKING:
    from litestar import Litestar


def socketify_run(app: Litestar) -> ASGI:
    ASGI(app, lifespan=True).listen(8009).run(workers=1, block=True)


if __name__ == "__main__":
    socketify_run(create_app())
