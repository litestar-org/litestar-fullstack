"""Email message classes for the email system.

This module provides dataclasses for representing email messages with support
for multiple recipients, attachments, and alternative content representations.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EmailMessage:
    """Represents an email message.

    This class provides a structured way to compose email messages with
    support for multiple recipients, CC/BCC, reply-to addresses, custom
    headers, attachments, and alternative content representations.

    Attributes:
        subject: Email subject line.
        body: Plain text email body.
        from_email: Sender email address. If None, uses default from settings.
        to: List of recipient email addresses.
        cc: List of CC recipient email addresses.
        bcc: List of BCC recipient email addresses.
        reply_to: List of reply-to email addresses.
        headers: Additional email headers as key-value pairs.
        attachments: List of (filename, content, mimetype) tuples.
        alternatives: List of (content, mimetype) tuples for alternative representations.

    Example:
        message = EmailMessage(
            subject="Welcome!",
            body="Welcome to our platform.",
            to=["user@example.com"],
        )
        message.attach_alternative("<h1>Welcome!</h1>", "text/html")
    """

    subject: str
    body: str
    from_email: str | None = None
    to: list[str] = field(default_factory=list)
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)
    reply_to: list[str] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)
    attachments: list[tuple[str, bytes, str]] = field(default_factory=list)
    alternatives: list[tuple[str, str]] = field(default_factory=list)

    def attach_alternative(self, content: str, mimetype: str) -> None:
        """Attach an alternative content representation.

        This is typically used to attach HTML content alongside the plain text body.

        Args:
            content: The alternative content (e.g., HTML string).
            mimetype: The MIME type of the content (e.g., "text/html").
        """
        self.alternatives.append((content, mimetype))

    def attach(self, filename: str, content: bytes, mimetype: str) -> None:
        """Attach a file to the email.

        Args:
            filename: The name of the attachment file.
            content: The binary content of the file.
            mimetype: The MIME type of the file (e.g., "application/pdf").
        """
        self.attachments.append((filename, content, mimetype))

    def recipients(self) -> list[str]:
        """Return a list of all recipients (to, cc, bcc combined).

        Returns:
            Combined list of all recipient email addresses.
        """
        return self.to + self.cc + self.bcc


@dataclass
class EmailMultiAlternatives(EmailMessage):
    """Email message with both plain text and HTML content.

    This is a convenience class that automatically attaches HTML content
    as an alternative to the plain text body.

    Attributes:
        html_body: HTML version of the email body. Automatically attached
            as an alternative if provided.

    Example:
        message = EmailMultiAlternatives(
            subject="Welcome!",
            body="Welcome to our platform.",  # Plain text
            html_body="<h1>Welcome!</h1>",     # HTML version
            to=["user@example.com"],
        )
    """

    html_body: str | None = None

    def __post_init__(self) -> None:
        """Automatically attach HTML body as alternative if provided."""
        if self.html_body:
            self.attach_alternative(self.html_body, "text/html")
