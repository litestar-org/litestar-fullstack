"""Unit tests for ``AppEmailService`` public delivery, rendering, escaping, and error behavior."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from uuid import uuid4

import pytest
from litestar import Litestar, post
from litestar.di import Provide
from litestar.testing import AsyncTestClient
from litestar_email import EmailConfig, EmailMultiAlternatives, EmailService, InMemoryBackend
from litestar_email.exceptions import EmailDeliveryError, EmailRateLimitError

from app.db import models as m
from app.lib.email import AppEmailService

if TYPE_CHECKING:
    from app.lib.email.service import UserProtocol

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
def clear_email_outbox() -> None:
    """Clear email outbox before each test."""
    InMemoryBackend.clear()


@pytest.fixture
def mailer() -> EmailService:
    """Create EmailService instance with in-memory backend."""
    return EmailService(config=EmailConfig(backend="memory"))


@pytest.fixture
def app_email_service(mailer: EmailService) -> AppEmailService:
    """Create AppEmailService instance."""
    return AppEmailService(mailer=mailer)


@pytest.fixture
def user() -> m.User:
    """Create test user."""
    return m.User(
        id=uuid4(),
        email="test@example.com",
        name="Test User",
        is_active=True,
        is_verified=False,
        is_superuser=False,
        login_count=0,
    )


@pytest.fixture
def user_without_name() -> m.User:
    """Create test user without name."""
    return m.User(
        id=uuid4(),
        email="noname@example.com",
        name=None,
        is_active=True,
        is_verified=False,
        is_superuser=False,
        login_count=0,
    )


@pytest.fixture
def verification_token() -> str:
    """Create test verification token."""
    return "test_verification_token_12345"


@pytest.fixture
def password_reset_token() -> str:
    """Create test password reset token."""
    return "test_reset_token_12345"


def _last_outbox_message() -> EmailMultiAlternatives:
    assert len(InMemoryBackend.outbox) >= 1
    message = InMemoryBackend.outbox[-1]
    assert isinstance(message, EmailMultiAlternatives)
    return message


async def test_app_email_service_initialization(mailer: EmailService) -> None:
    """AppEmailService initializes base_url and app_name from settings."""
    service = AppEmailService(mailer=mailer)
    assert isinstance(service.base_url, str)
    assert service.base_url
    assert isinstance(service.app_name, str)
    assert service.app_name


async def test_send_verification_email_renders_url_structure_and_security_copy(
    app_email_service: AppEmailService,
    user: m.User,
    user_without_name: m.User,
    verification_token: str,
) -> None:
    """Verification emails deliver HTML and plain-text bodies with URL, expiry, and security guidance."""
    result = await app_email_service.send_verification_email(cast("UserProtocol", user), verification_token)
    assert result is True
    message = _last_outbox_message()
    assert user.email in message.to
    assert "verify" in message.subject.lower()
    html = message.html_body or ""
    expected_url = f"{app_email_service.base_url}/verify-email?token={verification_token}"
    assert expected_url in html
    assert "verify your email" in html.lower()
    assert "24" in html
    assert "hours" in html.lower()
    assert app_email_service.app_name in html
    assert "didn't create an account" in html.lower() or "didn&#x27;t create an account" in html.lower()
    assert "safely" in html.lower()
    assert "ignore" in html.lower()
    assert "expire" in html.lower()
    assert "<" not in message.body
    assert ">" not in message.body

    result_no_name = await app_email_service.send_verification_email(
        cast("UserProtocol", user_without_name), verification_token
    )
    assert result_no_name is True
    assert len(InMemoryBackend.outbox) == 2


async def test_send_welcome_email_and_repeated_template_renders(
    app_email_service: AppEmailService,
    user: m.User,
) -> None:
    """Welcome emails render user-specific details across repeated deliveries."""
    assert await app_email_service.send_welcome_email(cast("UserProtocol", user)) is True
    first = _last_outbox_message()
    assert "welcome" in first.subject.lower()
    assert "Test User" in (first.html_body or "")
    assert app_email_service.app_name in (first.html_body or "")

    second_user = m.User(
        id=uuid4(),
        email="second@example.com",
        name="Second User",
        is_active=True,
        is_verified=True,
        is_superuser=False,
        login_count=0,
    )
    assert await app_email_service.send_welcome_email(cast("UserProtocol", second_user)) is True
    second = _last_outbox_message()
    assert "Second User" in (second.html_body or "")
    assert "Test User" not in (second.html_body or "")


async def test_send_password_reset_and_confirmation_emails(
    app_email_service: AppEmailService,
    user: m.User,
    password_reset_token: str,
) -> None:
    """Password reset and confirmation emails deliver expected subjects and reset links."""
    result = await app_email_service.send_password_reset_email(
        cast("UserProtocol", user),
        password_reset_token,
        expires_in_minutes=60,
    )
    assert result is True
    reset_msg = _last_outbox_message()
    assert "reset" in reset_msg.subject.lower()
    assert password_reset_token in (reset_msg.html_body or "")

    confirm_result = await app_email_service.send_password_reset_confirmation_email(cast("UserProtocol", user))
    assert confirm_result is True
    assert len(InMemoryBackend.outbox) == 2


async def test_send_team_invitation_email_validates_and_escapes_url(
    app_email_service: AppEmailService,
) -> None:
    """Team invitation email rejects non-HTTP(S) URLs and escapes special characters in valid URLs."""
    with pytest.raises(ValueError, match="http or https"):
        await app_email_service.send_team_invitation_email(
            invitee_email="invitee@example.com",
            inviter_name="Inviter User",
            team_name="Test Team",
            invitation_url="javascript:alert(1)",
        )

    result = await app_email_service.send_team_invitation_email(
        invitee_email="invitee@example.com",
        inviter_name="Inviter User",
        team_name="Test Team",
        invitation_url='https://example.com/accept-invite?a=1&b="x"',
    )
    assert result is True
    message = _last_outbox_message()
    assert "invitee@example.com" in message.to
    assert "Test Team" in message.subject
    html = message.html_body or ""
    assert "&quot;" in html
    assert "&amp;" in html


async def test_send_email_plain_text_fallback_strips_html(
    app_email_service: AppEmailService,
) -> None:
    """``send_email`` generates a stripped plain-text body when ``text_content`` is omitted."""
    sent = await app_email_service.send_email(
        to_email="plain@example.com",
        subject="Plain Fallback",
        html_content="<p>Hello <strong>World</strong></p>&nbsp;<a href='https://example.com'>Link</a>",
    )
    assert sent is True
    message = _last_outbox_message()
    assert "<" not in message.body
    assert ">" not in message.body
    assert "Hello" in message.body
    assert "World" in message.body
    assert "Link" in message.body


async def test_email_service_litestar_di_route_and_exception_specificity() -> None:
    """Litestar DI injects ``AppEmailService`` and propagates delivery/rate-limit exceptions."""
    email_cfg = EmailConfig(backend="memory", from_email="noreply@example.com")

    def provide_mailer() -> EmailService:
        return email_cfg.get_service()

    @post("/send-test")
    async def send_test(app_mailer: AppEmailService) -> dict[str, bool]:
        sent = await app_mailer.send_email(
            to_email="di@example.com",
            subject="DI Test",
            html_content="<p>Hello <b>DI</b></p>",
        )
        return {"sent": sent}

    app = Litestar(
        route_handlers=[send_test],
        dependencies={
            "mailer": Provide(provide_mailer, sync_to_thread=False),
            "app_mailer": Provide(AppEmailService, sync_to_thread=False),
        },
    )
    async with AsyncTestClient(app=app) as client:
        resp = await client.post("/send-test")
        assert resp.status_code == 201
        assert resp.json() == {"sent": True}
    assert len(InMemoryBackend.outbox) == 1
    assert InMemoryBackend.outbox[0].to == ["di@example.com"]

    class _RateLimitedMailer:
        async def send_message(self, message: Any) -> int:
            _ = message
            msg = "429 rate limited"
            raise EmailRateLimitError(msg)

    failing = AppEmailService(mailer=cast("EmailService", _RateLimitedMailer()))
    with pytest.raises(EmailRateLimitError):
        await failing.send_email(to_email="fail@example.com", subject="Fail", html_content="<p>x</p>")

    class _DeliveryFailedMailer:
        async def send_message(self, message: Any) -> int:
            _ = message
            msg = "550 bounce"
            raise EmailDeliveryError(msg)

    failing2 = AppEmailService(mailer=cast("EmailService", _DeliveryFailedMailer()))
    with pytest.raises(EmailDeliveryError):
        await failing2.send_email(to_email="fail@example.com", subject="Fail", html_content="<p>x</p>")
