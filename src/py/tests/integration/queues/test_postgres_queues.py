"""Integration tests for PostgreSQL ``litestar-queues`` enqueue, execution, admin API, and maintenance."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pytest
from litestar_email import EmailConfig, EmailMultiAlternatives
from litestar_queues import QueuePlugin, QueueService, Worker, WorkerConfig
from litestar_queues.maintenance import QueueMaintenanceService
from sqlalchemy import select

from app import config
from app.db import models as m
from app.domain.accounts.jobs import send_welcome_email_task
from app.domain.system.jobs import export_team_summary, scheduler_canary
from tests.integration.conftest import login_session_client, reset_client_session

if TYPE_CHECKING:
    from httpx import AsyncClient
    from litestar import Litestar
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [pytest.mark.anyio, pytest.mark.integration, pytest.mark.endpoints]


async def test_postgres_queue_enqueue_execute_and_email_delivery(
    app: Litestar,
    session: AsyncSession,
    test_team: m.Team,
    test_user: m.User,
    email_outbox: list[Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tasks enqueued into PostgreSQL execute via ``Worker.run_once`` and transition to completed."""
    monkeypatch.setattr(config, "email", EmailConfig(backend="memory"))
    queue_service = QueueService(config=app.plugins.get(QueuePlugin).config)
    await queue_service.open()
    try:
        report_result = await queue_service.enqueue(
            export_team_summary,
            team_id=str(test_team.id),
            requested_by_id=str(test_user.id),
            metadata={"requested_by_id": str(test_user.id), "team_id": str(test_team.id)},
        )
        welcome_result = await queue_service.enqueue(
            send_welcome_email_task,
            email=test_user.email,
            user_name=test_user.name,
        )
        canary_result = await queue_service.enqueue(scheduler_canary)

        worker = Worker(
            queue_service,
            config=WorkerConfig(
                queues=("reports", "emails", "maintenance"),
                max_concurrency=4,
                poll_interval=0.05,
            ),
        )
        for _ in range(4):
            ran = await worker.run_once()
            await worker.stop()
            if ran == 0:
                break

        for task_id in (report_result.id, welcome_result.id, canary_result.id):
            record = await queue_service.get_task(task_id)
            assert record is not None
            assert str(record.status) == "completed"
    finally:
        await queue_service.close()

    db_rows = (await session.scalars(select(m.QueueTask))).all()
    assert len(db_rows) >= 3
    assert any(
        isinstance(msg, EmailMultiAlternatives) and test_user.email in msg.to and msg.html_body for msg in email_outbox
    )


async def test_user_and_admin_queue_endpoints_with_cancellation(
    seeded_client: AsyncClient,
    test_user: m.User,
    test_team: m.Team,
) -> None:
    """Users can enqueue and list their own report tasks; superusers can inspect and cancel tasks."""
    user_csrf = await login_session_client(seeded_client, test_user.email, "TestPassword123!")
    enqueue_resp = await seeded_client.post(
        f"/api/queues/reports/team-summary/{test_team.id}",
        headers=user_csrf,
    )
    assert enqueue_resp.status_code == 201, enqueue_resp.text
    task_id = enqueue_resp.json()["taskId"]
    assert enqueue_resp.json()["queue"] == "reports"

    my_tasks = await seeded_client.get("/api/queues/tasks")
    assert my_tasks.status_code == 200
    assert task_id in [item["taskId"] for item in my_tasks.json()["items"]]

    assert (await seeded_client.get("/api/admin/queues/tasks")).status_code == 403

    reset_client_session(seeded_client)
    admin_csrf = await login_session_client(seeded_client, "superuser@example.com", "Test_Password1!")
    admin_list = await seeded_client.get("/api/admin/queues/tasks", params={"queue": "reports"})
    assert admin_list.status_code == 200
    assert task_id in [item["taskId"] for item in admin_list.json()["items"]]

    invalid_status = await seeded_client.get("/api/admin/queues/tasks", params={"status": "bogus"})
    assert invalid_status.status_code == 400

    cancel_resp = await seeded_client.post(f"/api/admin/queues/tasks/{task_id}/cancel", headers=admin_csrf)
    assert cancel_resp.status_code == 201, cancel_resp.text
    assert cancel_resp.json()["taskId"] == task_id
    assert cancel_resp.json()["cancelled"] is True


async def test_postgres_queue_maintenance_returns_structured_json(
    app: Litestar,
) -> None:
    """``QueueMaintenanceService.run`` executes against PostgreSQL and serializes a valid JSON summary."""
    queue_service = QueueService(config=app.plugins.get(QueuePlugin).config)
    await queue_service.open()
    try:
        maintenance_config = queue_service.config.maintenance
        assert maintenance_config is not None

        maintenance = QueueMaintenanceService(service=queue_service, config=maintenance_config)
        summary = await maintenance.run()
        serialized = json.dumps(summary.to_payload())
        parsed = json.loads(serialized)

        assert "outcome" in parsed
        assert "phases" in parsed
        assert isinstance(parsed["phases"], list)
    finally:
        await queue_service.close()
