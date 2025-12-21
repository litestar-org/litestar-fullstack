"""Async SMTP email backend using aiosmtplib."""

from __future__ import annotations

import logging
from email.message import EmailMessage as StdEmailMessage
from typing import TYPE_CHECKING, Any

import aiosmtplib

from app.lib.email.backends import register_backend
from app.lib.email.backends.base import BaseEmailBackend

if TYPE_CHECKING:
    from app.lib.email.base import EmailMessage

logger = logging.getLogger(__name__)


@register_backend("smtp")
class AsyncSMTPBackend(BaseEmailBackend):
    """Async SMTP email backend using aiosmtplib.

    This backend provides true async email sending without blocking the
    event loop. It supports connection pooling through the context manager
    protocol, TLS/SSL, and authentication.

    Example:
        EMAIL_BACKEND=smtp
        EMAIL_SMTP_HOST=smtp.example.com
        EMAIL_SMTP_PORT=587
        EMAIL_SMTP_USER=user
        EMAIL_SMTP_PASSWORD=pass
        EMAIL_USE_TLS=true

        # Connection pooling for bulk sending
        async with get_backend() as backend:
            await backend.send_messages([msg1, msg2, msg3])
    """

    def __init__(
        self,
        fail_silently: bool = False,
        host: str | None = None,
        port: int | None = None,
        username: str | None = None,
        password: str | None = None,
        use_tls: bool | None = None,
        use_ssl: bool | None = None,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize SMTP backend.

        Args:
            fail_silently: If True, suppress exceptions during send.
            host: SMTP server hostname. If None, uses settings.
            port: SMTP server port. If None, uses settings.
            username: SMTP username. If None, uses settings.
            password: SMTP password. If None, uses settings.
            use_tls: Whether to use STARTTLS. If None, uses settings.
            use_ssl: Whether to use implicit SSL. If None, uses settings.
            timeout: Connection timeout in seconds. If None, uses settings.
            **kwargs: Additional arguments (ignored).
        """
        super().__init__(fail_silently=fail_silently, **kwargs)

        from app.lib.settings import get_settings

        settings = get_settings().email

        self.host = host if host is not None else settings.SMTP_HOST
        self.port = port if port is not None else settings.SMTP_PORT
        self.username = username if username is not None else settings.SMTP_USER
        self.password = password if password is not None else settings.SMTP_PASSWORD
        self.use_tls = use_tls if use_tls is not None else settings.USE_TLS
        self.use_ssl = use_ssl if use_ssl is not None else settings.USE_SSL
        self.timeout = timeout if timeout is not None else settings.TIMEOUT or 30

        self.connection: aiosmtplib.SMTP | None = None

    async def open(self) -> bool:
        """Open a connection to the SMTP server.

        Returns:
            True if a new connection was opened, False if reusing existing.
        """
        if self.connection:
            return False

        self.connection = aiosmtplib.SMTP(
            hostname=self.host,
            port=self.port,
            timeout=self.timeout,
            use_tls=self.use_ssl,  # use_tls in aiosmtplib means implicit SSL
        )

        try:
            await self.connection.connect()

            if self.use_tls and not self.use_ssl:
                await self.connection.starttls()

            if self.username and self.password:
                await self.connection.login(self.username, self.password)
        except Exception:
            logger.exception("Failed to connect to SMTP server %s:%s", self.host, self.port)
            self.connection = None
            if not self.fail_silently:
                raise
            return False
        else:
            return True

    async def close(self) -> None:
        """Close the connection to the SMTP server."""
        if self.connection:
            try:
                await self.connection.quit()
            except Exception:
                logger.exception("Error closing SMTP connection")
                if not self.fail_silently:
                    raise
            finally:
                self.connection = None

    async def send_messages(self, messages: list[EmailMessage]) -> int:
        """Send messages via SMTP.

        If not already connected, opens a connection for the duration
        of the send operation.

        Args:
            messages: List of EmailMessage instances to send.

        Returns:
            Number of messages successfully sent.
        """
        if not messages:
            return 0

        # Use context manager if not already connected
        new_connection = await self.open()

        try:
            num_sent = 0
            for message in messages:
                try:
                    await self._send_message(message)
                    num_sent += 1
                except Exception:
                    logger.exception("Failed to send email to %s", message.to)
                    if not self.fail_silently:
                        raise
            return num_sent

        finally:
            if new_connection:
                await self.close()

    async def _send_message(self, message: EmailMessage) -> None:
        """Send a single message.

        Args:
            message: The email message to send.
        """
        if self.connection is None:
            err_msg = "SMTP connection not established"
            raise RuntimeError(err_msg)

        email_msg = self._build_message(message)
        await self.connection.send_message(email_msg)
        logger.info("Email sent to %s with subject: %s", message.to, message.subject)

    def _build_message(self, message: EmailMessage) -> StdEmailMessage:
        """Convert our EmailMessage to stdlib EmailMessage.

        Args:
            message: Our EmailMessage instance.

        Returns:
            Standard library EmailMessage instance.
        """
        from app.lib.settings import get_settings

        settings = get_settings().email

        msg = StdEmailMessage()
        msg["Subject"] = message.subject
        msg["From"] = message.from_email or settings.FROM_EMAIL
        msg["To"] = ", ".join(message.to)

        if message.cc:
            msg["Cc"] = ", ".join(message.cc)
        if message.reply_to:
            msg["Reply-To"] = ", ".join(message.reply_to)

        for key, value in message.headers.items():
            msg[key] = value

        # Set plain text body
        msg.set_content(message.body)

        # Add HTML alternative if present
        for content, mimetype in message.alternatives:
            if mimetype == "text/html":
                msg.add_alternative(content, subtype="html")

        # Add attachments
        for filename, attach_content, mimetype in message.attachments:
            maintype, subtype = mimetype.split("/", 1)
            msg.add_attachment(attach_content, maintype=maintype, subtype=subtype, filename=filename)

        return msg
