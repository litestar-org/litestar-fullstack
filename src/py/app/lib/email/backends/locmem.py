"""In-memory email backend for testing."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from app.lib.email.backends import register_backend
from app.lib.email.backends.base import BaseEmailBackend

if TYPE_CHECKING:
    from app.lib.email.base import EmailMessage


@register_backend("locmem")
class InMemoryBackend(BaseEmailBackend):
    """In-memory email backend for testing.

    All sent emails are stored in the class-level `outbox` list for inspection
    in tests. This allows test assertions on email subject, recipients, body,
    headers, and attachments.

    The outbox is shared across all instances and should be cleared between
    tests using the `clear()` class method.

    Example:
        # In settings
        EMAIL_BACKEND=locmem

        # In tests
        from app.lib.email.backends.locmem import InMemoryBackend

        def test_email_sent():
            InMemoryBackend.clear()

            # Code that sends email
            await send_welcome_email(user)

            # Assertions
            assert len(InMemoryBackend.outbox) == 1
            assert InMemoryBackend.outbox[0].subject == "Welcome!"
            assert "user@example.com" in InMemoryBackend.outbox[0].to
    """

    outbox: ClassVar[list[EmailMessage]] = []

    def __init__(self, fail_silently: bool = False, **kwargs: Any) -> None:
        """Initialize in-memory backend.

        Args:
            fail_silently: If True, suppress exceptions during send.
            **kwargs: Additional arguments (ignored).
        """
        super().__init__(fail_silently=fail_silently, **kwargs)

    async def send_messages(self, messages: list[EmailMessage]) -> int:
        """Store messages in the outbox.

        Args:
            messages: List of EmailMessage instances to store.

        Returns:
            Number of messages stored.
        """
        self.outbox.extend(messages)
        return len(messages)

    @classmethod
    def clear(cls) -> None:
        """Clear all stored messages.

        Call this method in test setup or teardown to ensure a clean
        state between tests.
        """
        cls.outbox.clear()
