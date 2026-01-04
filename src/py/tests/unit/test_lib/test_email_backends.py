"""Comprehensive tests for email backends."""

from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.lib.email.backends import get_backend
from app.lib.email.backends.console import ConsoleBackend
from app.lib.email.backends.locmem import InMemoryBackend
from app.lib.email.base import EmailMessage

if TYPE_CHECKING:
    pass

pytestmark = [pytest.mark.unit, pytest.mark.email]


class TestConsoleBackend:
    """Test ConsoleBackend."""

    def test_init_default_stream(self) -> None:
        """Test initialization with default stream (stdout)."""
        import sys

        backend = ConsoleBackend()

        assert backend.stream is sys.stdout
        assert backend.fail_silently is False

    def test_init_custom_stream(self) -> None:
        """Test initialization with custom stream."""
        stream = StringIO()
        backend = ConsoleBackend(stream=stream)

        assert backend.stream is stream

    def test_init_fail_silently(self) -> None:
        """Test initialization with fail_silently flag."""
        backend = ConsoleBackend(fail_silently=True)

        assert backend.fail_silently is True

    @pytest.mark.asyncio
    async def test_send_empty_messages(self) -> None:
        """Test sending empty list of messages."""
        stream = StringIO()
        backend = ConsoleBackend(stream=stream)

        result = await backend.send_messages([])

        assert result == 0
        assert stream.getvalue() == ""

    @pytest.mark.asyncio
    async def test_send_single_message(self) -> None:
        """Test sending a single message."""
        stream = StringIO()
        backend = ConsoleBackend(stream=stream)

        message = EmailMessage(
            subject="Test Subject",
            body="Test body content",
            to=["recipient@example.com"],
            from_email="sender@example.com",
        )

        with patch("app.lib.settings.get_settings") as mock_settings:
            mock_settings.return_value.email.FROM_EMAIL = "default@example.com"
            result = await backend.send_messages([message])

        assert result == 1
        output = stream.getvalue()
        assert "Test Subject" in output
        assert "Test body content" in output
        assert "recipient@example.com" in output
        assert "sender@example.com" in output

    @pytest.mark.asyncio
    async def test_send_multiple_messages(self) -> None:
        """Test sending multiple messages."""
        stream = StringIO()
        backend = ConsoleBackend(stream=stream)

        messages = [
            EmailMessage(
                subject=f"Subject {i}",
                body=f"Body {i}",
                to=[f"recipient{i}@example.com"],
                from_email="sender@example.com",
            )
            for i in range(3)
        ]

        with patch("app.lib.settings.get_settings") as mock_settings:
            mock_settings.return_value.email.FROM_EMAIL = "default@example.com"
            result = await backend.send_messages(messages)

        assert result == 3
        output = stream.getvalue()
        for i in range(3):
            assert f"Subject {i}" in output
            assert f"Body {i}" in output
            assert f"recipient{i}@example.com" in output

    @pytest.mark.asyncio
    async def test_message_with_cc(self) -> None:
        """Test message with CC recipients."""
        stream = StringIO()
        backend = ConsoleBackend(stream=stream)

        message = EmailMessage(
            subject="Test",
            body="Body",
            to=["to@example.com"],
            cc=["cc1@example.com", "cc2@example.com"],
        )

        with patch("app.lib.settings.get_settings") as mock_settings:
            mock_settings.return_value.email.FROM_EMAIL = "default@example.com"
            await backend.send_messages([message])

        output = stream.getvalue()
        assert "Cc:" in output
        assert "cc1@example.com" in output
        assert "cc2@example.com" in output

    @pytest.mark.asyncio
    async def test_message_with_bcc(self) -> None:
        """Test message with BCC recipients."""
        stream = StringIO()
        backend = ConsoleBackend(stream=stream)

        message = EmailMessage(
            subject="Test",
            body="Body",
            to=["to@example.com"],
            bcc=["bcc@example.com"],
        )

        with patch("app.lib.settings.get_settings") as mock_settings:
            mock_settings.return_value.email.FROM_EMAIL = "default@example.com"
            await backend.send_messages([message])

        output = stream.getvalue()
        assert "Bcc:" in output
        assert "bcc@example.com" in output

    @pytest.mark.asyncio
    async def test_message_with_reply_to(self) -> None:
        """Test message with reply-to address."""
        stream = StringIO()
        backend = ConsoleBackend(stream=stream)

        message = EmailMessage(
            subject="Test",
            body="Body",
            to=["to@example.com"],
            reply_to=["reply@example.com"],
        )

        with patch("app.lib.settings.get_settings") as mock_settings:
            mock_settings.return_value.email.FROM_EMAIL = "default@example.com"
            await backend.send_messages([message])

        output = stream.getvalue()
        assert "Reply-To:" in output
        assert "reply@example.com" in output

    @pytest.mark.asyncio
    async def test_message_with_headers(self) -> None:
        """Test message with custom headers."""
        stream = StringIO()
        backend = ConsoleBackend(stream=stream)

        message = EmailMessage(
            subject="Test",
            body="Body",
            to=["to@example.com"],
            headers={"X-Custom-Header": "custom-value", "X-Another": "another-value"},
        )

        with patch("app.lib.settings.get_settings") as mock_settings:
            mock_settings.return_value.email.FROM_EMAIL = "default@example.com"
            await backend.send_messages([message])

        output = stream.getvalue()
        assert "X-Custom-Header: custom-value" in output
        assert "X-Another: another-value" in output

    @pytest.mark.asyncio
    async def test_message_with_alternatives(self) -> None:
        """Test message with HTML alternative."""
        stream = StringIO()
        backend = ConsoleBackend(stream=stream)

        message = EmailMessage(
            subject="Test",
            body="Plain text body",
            to=["to@example.com"],
        )
        message.alternatives = [("<html><body>HTML body</body></html>", "text/html")]

        with patch("app.lib.settings.get_settings") as mock_settings:
            mock_settings.return_value.email.FROM_EMAIL = "default@example.com"
            await backend.send_messages([message])

        output = stream.getvalue()
        assert "Plain text body" in output
        assert "Alternative (text/html):" in output
        assert "HTML body" in output

    @pytest.mark.asyncio
    async def test_message_with_attachments(self) -> None:
        """Test message with attachments."""
        stream = StringIO()
        backend = ConsoleBackend(stream=stream)

        message = EmailMessage(
            subject="Test",
            body="Body",
            to=["to@example.com"],
        )
        message.attachments = [
            ("document.pdf", b"pdf content", "application/pdf"),
            ("image.png", b"png content", "image/png"),
        ]

        with patch("app.lib.settings.get_settings") as mock_settings:
            mock_settings.return_value.email.FROM_EMAIL = "default@example.com"
            await backend.send_messages([message])

        output = stream.getvalue()
        assert "Attachments: 2" in output
        assert "document.pdf (application/pdf)" in output
        assert "image.png (image/png)" in output

    @pytest.mark.asyncio
    async def test_uses_default_from_email(self) -> None:
        """Test that default from email is used when not specified."""
        stream = StringIO()
        backend = ConsoleBackend(stream=stream)

        message = EmailMessage(
            subject="Test",
            body="Body",
            to=["to@example.com"],
            from_email=None,  # Not specified
        )

        with patch("app.lib.settings.get_settings") as mock_settings:
            mock_settings.return_value.email.FROM_EMAIL = "default@example.com"
            await backend.send_messages([message])

        output = stream.getvalue()
        assert "From: default@example.com" in output

    @pytest.mark.asyncio
    async def test_stream_flush(self) -> None:
        """Test that stream is flushed after writing."""
        stream = Mock()
        stream.write = Mock()
        stream.flush = Mock()
        backend = ConsoleBackend(stream=stream)

        message = EmailMessage(
            subject="Test",
            body="Body",
            to=["to@example.com"],
        )

        with patch("app.lib.settings.get_settings") as mock_settings:
            mock_settings.return_value.email.FROM_EMAIL = "default@example.com"
            await backend.send_messages([message])

        stream.flush.assert_called()


class TestInMemoryBackend:
    """Test InMemoryBackend (in-memory email backend)."""

    def setup_method(self) -> None:
        """Clear outbox before each test."""
        InMemoryBackend.clear()

    def test_init(self) -> None:
        """Test initialization."""
        backend = InMemoryBackend()
        assert backend.fail_silently is False

    @pytest.mark.asyncio
    async def test_send_stores_messages(self) -> None:
        """Test that messages are stored in memory."""
        backend = InMemoryBackend()

        message1 = EmailMessage(
            subject="Subject 1",
            body="Body 1",
            to=["to1@example.com"],
        )
        message2 = EmailMessage(
            subject="Subject 2",
            body="Body 2",
            to=["to2@example.com"],
        )

        await backend.send_messages([message1])
        await backend.send_messages([message2])

        # Messages should be accessible via the outbox
        assert len(InMemoryBackend.outbox) == 2
        assert InMemoryBackend.outbox[0] is message1
        assert InMemoryBackend.outbox[1] is message2

    @pytest.mark.asyncio
    async def test_send_returns_count(self) -> None:
        """Test that send returns message count."""
        backend = InMemoryBackend()

        messages = [
            EmailMessage(subject=f"Subject {i}", body=f"Body {i}", to=[f"to{i}@example.com"]) for i in range(5)
        ]

        result = await backend.send_messages(messages)

        assert result == 5

    @pytest.mark.asyncio
    async def test_empty_messages(self) -> None:
        """Test sending empty list."""
        backend = InMemoryBackend()

        result = await backend.send_messages([])

        assert result == 0
        assert len(InMemoryBackend.outbox) == 0

    def test_clear_outbox(self) -> None:
        """Test clearing the outbox."""
        # Add a message directly to outbox for testing
        message = EmailMessage(subject="Test", body="Body", to=["to@example.com"])
        InMemoryBackend.outbox.append(message)

        assert len(InMemoryBackend.outbox) == 1

        InMemoryBackend.clear()

        assert len(InMemoryBackend.outbox) == 0


class TestGetBackend:
    """Test get_backend factory function."""

    def test_get_console_backend(self) -> None:
        """Test getting console backend from settings."""
        with patch("app.lib.settings.get_settings") as mock_settings:
            mock_settings.return_value.email.BACKEND = "console"
            backend = get_backend()
            assert isinstance(backend, ConsoleBackend)

    def test_get_locmem_backend(self) -> None:
        """Test getting locmem backend from settings."""
        with patch("app.lib.settings.get_settings") as mock_settings:
            mock_settings.return_value.email.BACKEND = "locmem"
            backend = get_backend()
            assert isinstance(backend, InMemoryBackend)

    def test_get_backend_with_fail_silently(self) -> None:
        """Test getting backend with fail_silently kwarg."""
        with patch("app.lib.settings.get_settings") as mock_settings:
            mock_settings.return_value.email.BACKEND = "console"
            backend = get_backend(fail_silently=True)

            assert isinstance(backend, ConsoleBackend)
            assert backend.fail_silently is True

    def test_get_backend_with_custom_kwargs(self) -> None:
        """Test getting backend with custom kwargs."""
        stream = StringIO()
        with patch("app.lib.settings.get_settings") as mock_settings:
            mock_settings.return_value.email.BACKEND = "console"
            backend = get_backend(stream=stream)

            assert isinstance(backend, ConsoleBackend)
            assert backend.stream is stream

    def test_get_unknown_backend(self) -> None:
        """Test getting unknown backend raises error."""
        with patch("app.lib.settings.get_settings") as mock_settings:
            mock_settings.return_value.email.BACKEND = "unknown_backend"
            with pytest.raises(KeyError, match="Unknown email backend"):
                get_backend()


class TestEmailMessage:
    """Test EmailMessage class."""

    def test_create_simple_message(self) -> None:
        """Test creating a simple email message."""
        message = EmailMessage(
            subject="Test Subject",
            body="Test body",
            to=["recipient@example.com"],
        )

        assert message.subject == "Test Subject"
        assert message.body == "Test body"
        assert message.to == ["recipient@example.com"]

    def test_create_message_with_all_fields(self) -> None:
        """Test creating message with all fields."""
        message = EmailMessage(
            subject="Full Subject",
            body="Full body",
            to=["to@example.com"],
            from_email="from@example.com",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            reply_to=["reply@example.com"],
            headers={"X-Custom": "value"},
        )

        assert message.from_email == "from@example.com"
        assert message.cc == ["cc@example.com"]
        assert message.bcc == ["bcc@example.com"]
        assert message.reply_to == ["reply@example.com"]
        assert message.headers == {"X-Custom": "value"}

    def test_message_defaults(self) -> None:
        """Test message default values."""
        message = EmailMessage(
            subject="Subject",
            body="Body",
            to=["to@example.com"],
        )

        assert message.cc == []
        assert message.bcc == []
        assert message.reply_to == []
        assert message.headers == {}
        assert message.alternatives == []
        assert message.attachments == []

    def test_add_alternative(self) -> None:
        """Test adding alternative content."""
        message = EmailMessage(
            subject="Subject",
            body="Plain text",
            to=["to@example.com"],
        )

        message.alternatives.append(("<p>HTML</p>", "text/html"))

        assert len(message.alternatives) == 1
        assert message.alternatives[0] == ("<p>HTML</p>", "text/html")

    def test_add_attachment(self) -> None:
        """Test adding attachment."""
        message = EmailMessage(
            subject="Subject",
            body="Body",
            to=["to@example.com"],
        )

        message.attachments.append(("file.txt", b"content", "text/plain"))

        assert len(message.attachments) == 1
        assert message.attachments[0] == ("file.txt", b"content", "text/plain")
