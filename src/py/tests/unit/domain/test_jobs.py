"""Unit tests for background and scheduled @task jobs."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from advanced_alchemy.base import orm_registry
from litestar_email import EmailConfig, InMemoryBackend
from litestar_queues import NonRetryableError, QueueConfig, QueueService, WorkerConfig
from sqlalchemy import select

from app import config as app_config
from app.db import models as m
from app.domain.accounts.jobs import (
    send_team_invitation_email_task,
    send_verification_email_task,
)
from app.domain.accounts.jobs._oauth_refresh import run_refresh_oauth_tokens
from app.domain.system.jobs import (
    export_team_summary,
    run_cleanup_auth_tokens,
    run_export_team_summary,
    scheduler_canary,
)
from app.lib.settings import AppSettings, DatabaseSettings, Settings

if TYPE_CHECKING:
    from pathlib import Path

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

pytestmark = pytest.mark.anyio


async def _make_db(tmp_path: Path, name: str) -> SQLAlchemyAsyncConfig:
    db_cfg = DatabaseSettings(URL=f"sqlite+aiosqlite:///{tmp_path / name}").get_config()
    async with db_cfg.get_engine().begin() as conn:
        await conn.run_sync(orm_registry.metadata.create_all)
    return db_cfg


async def test_email_queue_tasks_deliver_to_inmemory_outbox(monkeypatch: pytest.MonkeyPatch) -> None:
    InMemoryBackend.clear()
    monkeypatch.setattr(app_config, "email", EmailConfig(backend="memory", from_email="noreply@example.com"))

    sent_verify = await send_verification_email_task(
        email="alice@example.com",
        token="verify-tok-123",
        user_name="Alice",
    )
    sent_invite = await send_team_invitation_email_task(
        invitee_email="bob@example.com",
        inviter_name="Alice",
        team_name="Core Team",
        invitation_url="https://app.example.com/invite/abc",
    )

    assert sent_verify is True
    assert sent_invite is True
    assert len(InMemoryBackend.outbox) == 2
    assert InMemoryBackend.outbox[0].to == ["alice@example.com"]
    assert InMemoryBackend.outbox[1].to == ["bob@example.com"]


async def test_cleanup_auth_tokens_prunes_expired_tokens_and_rate_limit_store(tmp_path: Path) -> None:
    db_cfg = await _make_db(tmp_path, "cleanup_jobs.sqlite3")
    now = datetime.now(UTC)
    expired = now - timedelta(hours=2)
    future = now + timedelta(hours=2)

    async with db_cfg.get_session() as session:
        session.add_all(
            [
                m.PurposeToken(
                    token_id="tok-expired",
                    token_hash="a" * 64,
                    purpose="verify",
                    expires_at=expired,
                ),
                m.PurposeToken(
                    token_id="tok-live",
                    token_hash="b" * 64,
                    purpose="verify",
                    expires_at=future,
                ),
                m.AppStore(
                    namespace="rate_limit",
                    key="rl:expired",
                    value=b"1",
                    expires_at=expired,
                ),
                m.AppStore(
                    namespace="rate_limit",
                    key="rl:live",
                    value=b"1",
                    expires_at=future,
                ),
            ]
        )
        await session.commit()

    counts = await run_cleanup_auth_tokens(db_cfg)
    assert counts["purpose_tokens"] == 1
    assert counts["rate_limit_entries"] == 1

    async with db_cfg.get_session() as session:
        remaining_tokens = (await session.scalars(select(m.PurposeToken.token_id))).all()
        assert list(remaining_tokens) == ["tok-live"]
        remaining_rl = (
            await session.scalars(select(m.AppStore.key).where(m.AppStore.namespace == "rate_limit"))
        ).all()
        assert list(remaining_rl) == ["rl:live"]

    canary = await scheduler_canary()
    assert canary["status"] == "ok"


async def test_export_team_summary_and_missing_team_non_retryable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_cfg = await _make_db(tmp_path, "reports_jobs.sqlite3")
    monkeypatch.setattr(app_config, "alchemy", db_cfg)

    async with db_cfg.get_session() as session:
        user = m.User(email="owner@example.com", name="Owner", is_active=True, is_verified=True)
        team = m.Team(name="Platform", slug="platform")
        tag = m.Tag(name="backend", slug="backend")
        team.tags.append(tag)
        session.add_all([user, team, tag])
        await session.flush()
        session.add(m.TeamMember(user_id=user.id, team_id=team.id, role=m.TeamRoles.ADMIN, is_owner=True))
        await session.commit()
        team_id = str(team.id)
        user_id = str(user.id)

    queue_service = QueueService(
        config=QueueConfig(
            queue_backend="memory",
            execution_backend="immediate",
            worker=WorkerConfig(placement="external"),
        )
    )
    await queue_service.open()
    try:
        record = await queue_service.enqueue(
            export_team_summary,
            team_id=team_id,
            requested_by_id=user_id,
        )
        assert record.status == "completed"
        assert record.result is not None
        assert record.result["team_name"] == "Platform"
        assert record.result["member_count"] == 1
        assert record.result["tag_count"] == 1
    finally:
        await queue_service.close()

    with pytest.raises(NonRetryableError):
        await run_export_team_summary(db_cfg, team_id=str(uuid4()), requested_by_id=user_id)


async def test_refresh_oauth_tokens_with_no_configured_providers(tmp_path: Path) -> None:
    db_cfg = await _make_db(tmp_path, "oauth_refresh.sqlite3")
    settings = Settings(app=AppSettings(SECRET_KEY="refresh-test-secret"))
    result = await run_refresh_oauth_tokens(db_cfg, settings=settings)
    assert result == {"processed": 0, "refreshed": 0, "skipped": 0, "failed": 0}
