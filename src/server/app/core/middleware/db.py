import logging
from typing import TYPE_CHECKING

from starlite import ScopeType
from starlite.middleware import MiddlewareProtocol

from app.db import AsyncScopedSession

if TYPE_CHECKING:
    from starlite.types import ASGIApp, Message, Receive, Scope, Send


__all__ = ["DatabaseSessionMiddleware"]

logger = logging.getLogger(__name__)


class DatabaseSessionMiddleware(MiddlewareProtocol):
    def __init__(self, app: "ASGIApp") -> None:
        self.app = app

    @staticmethod
    async def _manage_session(message: "Message") -> None:
        logger.debug("_manage_session() called: %s", message)
        if 200 <= message["status"] < 300:  # type: ignore[typeddict-item]
            await AsyncScopedSession.commit()
            logger.debug("session committed")
        else:
            await AsyncScopedSession.rollback()
            logger.debug("database session rolled back")
        await AsyncScopedSession.remove()
        logger.debug("database session removed")

    async def __call__(self, scope: "Scope", receive: "Receive", send: "Send") -> None:
        if scope["type"] == ScopeType.HTTP:

            async def send_wrapper(message: "Message") -> None:
                if message["type"] == "http.response.start":
                    await self._manage_session(message)
                await send(message)

            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)
