"""Console email backend for development."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, TextIO

from app.lib.email.backends import register_backend
from app.lib.email.backends.base import BaseEmailBackend

if TYPE_CHECKING:
    from app.lib.email.base import EmailMessage


@register_backend("console")
class ConsoleBackend(BaseEmailBackend):
    """Email backend that writes emails to the console.

    This backend is useful for local development where you want to see
    the full email content without actually sending emails.

    The output includes all email metadata (from, to, subject, headers)
    and both plain text and HTML content.

    Example:
        EMAIL_BACKEND=console
        # or
        EMAIL_BACKEND=app.lib.email.backends.console.ConsoleBackend
    """

    def __init__(self, fail_silently: bool = False, stream: TextIO | None = None, **kwargs: Any) -> None:
        """Initialize console backend.

        Args:
            fail_silently: If True, suppress exceptions during send.
            stream: Output stream to write to. Defaults to sys.stdout.
            **kwargs: Additional arguments (ignored).
        """
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.stream = stream or sys.stdout

    async def send_messages(self, messages: list[EmailMessage]) -> int:
        """Write emails to the console.

        Args:
            messages: List of EmailMessage instances to output.

        Returns:
            Number of messages written.
        """
        if not messages:
            return 0

        msg_count = 0
        for message in messages:
            self._write_message(message)
            msg_count += 1

        return msg_count

    def _write_message(self, message: EmailMessage) -> None:
        """Write a single message to the stream.

        Args:
            message: The email message to write.
        """
        from app.lib.settings import get_settings

        settings = get_settings()
        separator = "-" * 79

        self.stream.write(f"{separator}\n")
        self.stream.write(f"From: {message.from_email or settings.email.FROM_EMAIL}\n")
        self.stream.write(f"To: {', '.join(message.to)}\n")

        if message.cc:
            self.stream.write(f"Cc: {', '.join(message.cc)}\n")
        if message.bcc:
            self.stream.write(f"Bcc: {', '.join(message.bcc)}\n")
        if message.reply_to:
            self.stream.write(f"Reply-To: {', '.join(message.reply_to)}\n")

        self.stream.write(f"Subject: {message.subject}\n")

        for header, value in message.headers.items():
            self.stream.write(f"{header}: {value}\n")

        self.stream.write(f"{separator}\n")
        self.stream.write("Body (text/plain):\n")
        self.stream.write(f"{message.body}\n")

        for content, mimetype in message.alternatives:
            self.stream.write(f"{separator}\n")
            self.stream.write(f"Alternative ({mimetype}):\n")
            self.stream.write(f"{content}\n")

        if message.attachments:
            self.stream.write(f"{separator}\n")
            self.stream.write(f"Attachments: {len(message.attachments)}\n")
            for filename, _content, mimetype in message.attachments:
                self.stream.write(f"  - {filename} ({mimetype})\n")

        self.stream.write(f"{separator}\n\n")
        self.stream.flush()
