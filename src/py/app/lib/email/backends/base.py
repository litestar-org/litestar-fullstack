"""Abstract base class for email backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from types import TracebackType

    from app.lib.email.base import EmailMessage


class BaseEmailBackend(ABC):
    """Abstract base class for email backends.

    All email backends must implement this interface. Backends are async-first
    to avoid blocking the Litestar event loop.

    The backend supports context manager protocol for connection pooling:

        async with get_backend() as backend:
            await backend.send_messages([msg1, msg2])

    Subclasses should override:
        - send_messages(): Required. Implement the actual sending logic.
        - open(): Optional. Open a connection to the mail server.
        - close(): Optional. Close the connection to the mail server.

    Attributes:
        fail_silently: If True, suppress exceptions during send operations.
    """

    def __init__(self, fail_silently: bool = False, **kwargs: Any) -> None:
        """Initialize the backend.

        Args:
            fail_silently: If True, suppress exceptions during send.
            **kwargs: Additional backend-specific configuration.
        """
        self.fail_silently = fail_silently

    async def open(self) -> bool:
        """Open a connection to the mail server.

        This method is called automatically when using the backend as a
        context manager. Override this method to implement connection pooling.

        Returns:
            True if a new connection was opened, False if reusing existing.
        """
        return True

    async def close(self) -> None:  # noqa: B027
        """Close the connection to the mail server.

        This method is called automatically when exiting the context manager.
        Override this method to properly close connections.
        """

    @abstractmethod
    async def send_messages(self, messages: list[EmailMessage]) -> int:
        """Send one or more EmailMessage objects.

        This is the main method that subclasses must implement. It should
        handle the actual delivery of emails through the backend's mechanism.

        Args:
            messages: List of EmailMessage instances to send.

        Returns:
            Number of messages successfully sent.

        Raises:
            Exception: If fail_silently is False and sending fails.
        """
        raise NotImplementedError

    async def __aenter__(self) -> Self:
        """Enter async context manager, opening the connection."""
        await self.open()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context manager, closing the connection."""
        await self.close()
