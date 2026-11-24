"""Integration tests verifying email URLs emitted by queued team and auth email tasks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from litestar_email import EmailConfig, EmailMultiAlternatives
from litestar_queues import QueuePlugin, QueueService, Worker, WorkerConfig

from app import config
from app.db import models as m
from app.domain.accounts.jobs import send_password_reset_email_task, send_verification_email_task
from app.lib.settings import get_settings

if TYPE_CHECKING:
    from httpx import AsyncClient
    from litestar import Litestar

pytestmark = [pytest.mark.anyio, pytest.mark.integration, pytest.mark.teams, pytest.mark.email]


async def test_team_invitation_queued_email_contains_app_url(
    app: Litestar,
    authenticated_client: AsyncClient,
    test_team: m.Team,
    email_outbox: list[Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Creating a team invitation enqueues a task whose worker execution renders the configured app URL."""
    monkeypatch.setattr(config, "email", EmailConfig(backend="memory"))
    app_url = get_settings().app.URL.rstrip("/")

    response = await authenticated_client.post(
        f"/api/teams/{test_team.id}/invitations",
        json={"email": "newmember@example.com", "role": m.TeamRoles.MEMBER.value},
    )
    assert response.status_code == 201, response.text
    invitation_id = response.json()["id"]

    queue_service = QueueService(config=app.plugins.get(QueuePlugin).config)
    await queue_service.open()
    try:
        worker = Worker(
            queue_service,
            config=WorkerConfig(queues=("emails",), max_concurrency=1, poll_interval=0.05),
        )
        processed = await worker.run_once()
        await worker.stop()
        assert processed >= 1
    finally:
        await queue_service.close()

    assert len(email_outbox) == 1
    message = email_outbox[0]
    assert isinstance(message, EmailMultiAlternatives)
    assert message.html_body is not None
    expected_path = f"{app_url}/teams/{test_team.id}/invitations/{invitation_id}"
    assert expected_path in message.html_body
    assert "example.com" not in message.html_body


async def test_auth_email_tasks_render_configured_app_urls(
    app: Litestar,
    email_outbox: list[Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Queued verification and password-reset tasks render links rooted at ``settings.app.URL``."""
    monkeypatch.setattr(config, "email", EmailConfig(backend="memory"))
    app_url = get_settings().app.URL.rstrip("/")

    queue_service = QueueService(config=app.plugins.get(QueuePlugin).config)
    await queue_service.open()
    try:
        await queue_service.enqueue(
            send_verification_email_task,
            email="verify-url@example.com",
            token="verify-token-123",
        )
        await queue_service.enqueue(
            send_password_reset_email_task,
            email="reset-url@example.com",
            token="reset-token-456",
        )

        worker = Worker(
            queue_service,
            config=WorkerConfig(queues=("emails",), max_concurrency=2, poll_interval=0.05),
        )
        processed = 0
        for _ in range(4):
            ran = await worker.run_once()
            await worker.stop()
            processed += ran
            if len(email_outbox) >= 2:
                break
    finally:
        await queue_service.close()

    assert processed >= 2
    assert len(email_outbox) == 2
    bodies = [msg.html_body or "" for msg in email_outbox]
    assert any(f"{app_url}/verify-email" in body and "verify-token-123" in body for body in bodies)
    assert any(f"{app_url}/reset-password" in body and "reset-token-456" in body for body in bodies)
