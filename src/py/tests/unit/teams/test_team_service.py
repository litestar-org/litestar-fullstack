"""Unit tests for TeamServices ServiceGroup, slug collision handling, ownership transfer, and invitation queue task."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from advanced_alchemy.base import orm_registry
from advanced_alchemy.filters import LimitOffsetFilter, OrderByFilter
from litestar_email import EmailConfig, InMemoryBackend
from litestar_queues import QueueConfig, QueuedBackgroundTask, QueueService, WorkerConfig

from app import config as app_config
from app.db import models as m
from app.domain import teams as teams_pkg
from app.domain.accounts.jobs import send_team_invitation_email_task
from app.domain.teams.services import TeamServices
from app.lib.settings import DatabaseSettings

if TYPE_CHECKING:
    from pathlib import Path

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

pytestmark = pytest.mark.anyio


async def _init_db(tmp_path: Path, name: str) -> SQLAlchemyAsyncConfig:
    db_cfg = DatabaseSettings(URL=f"sqlite+aiosqlite:///{tmp_path / name}").get_config()
    async with db_cfg.get_engine().begin() as conn:
        await conn.run_sync(orm_registry.metadata.create_all)
    return db_cfg


async def test_team_services_group_slugs_tags_and_ownership_transfer(tmp_path: Path) -> None:
    assert "listeners" not in teams_pkg.__all__

    db_cfg = await _init_db(tmp_path, "team_services.sqlite3")
    async with db_cfg.get_session() as session:
        owner = m.User(email="owner@example.com", name="Owner", is_active=True, is_verified=True)
        successor = m.User(email="successor@example.com", name="Successor", is_active=True, is_verified=True)
        session.add_all([owner, successor])
        await session.commit()
        owner_id = owner.id
        successor_id = successor.id

    async with TeamServices.new(config=db_cfg) as svc:
        team1 = await svc.teams.create(
            {"name": "Core Engineering", "owner_id": owner_id, "tags": ["platform", "backend"]},
            auto_commit=True,
        )
        team2 = await svc.teams.create(
            {"name": "Core Engineering", "owner_id": owner_id},
            auto_commit=True,
        )
        assert team1.slug == "core-engineering"
        assert team2.slug != team1.slug
        assert team2.slug.startswith("core-engineering")

        await svc.members.create(
            {"team_id": team1.id, "user_id": successor_id, "role": m.TeamRoles.MEMBER, "is_owner": False},
            auto_commit=True,
        )
        await svc.teams.update(item_id=team1.id, data={"owner_id": successor_id}, auto_commit=True)

        listed, total = await svc.teams.get_many_and_count(
            LimitOffsetFilter(limit=10, offset=0),
            OrderByFilter(field_name="name", sort_order="asc"),
        )
        assert total == 2
        assert len(listed) == 2
        team1_id = team1.id

    async with TeamServices.new(config=db_cfg) as fresh_svc:
        members = await fresh_svc.members.get_many(m.TeamMember.team_id == team1_id)
        by_user = {member.user_id: member for member in members}
        assert by_user[successor_id].is_owner is True
        assert by_user[successor_id].role == m.TeamRoles.ADMIN
        assert by_user[owner_id].is_owner is False

        from uuid import uuid4

        from advanced_alchemy.exceptions import RepositoryError

        with pytest.raises(RepositoryError):
            await fresh_svc.teams.update(item_id=team1_id, data={"owner_id": uuid4()}, auto_commit=True)
        await fresh_svc.session.rollback()

        unchanged = await fresh_svc.teams.update(
            item_id=team1_id,
            data={"name": "Core Engineering"},
            auto_commit=True,
        )
        assert unchanged.slug == "core-engineering"


async def test_queued_background_task_executes_team_invitation_email(monkeypatch: pytest.MonkeyPatch) -> None:
    InMemoryBackend.clear()
    monkeypatch.setattr(app_config, "email", EmailConfig(backend="memory", from_email="noreply@example.com"))
    queue_svc = QueueService(
        config=QueueConfig(
            queue_backend="memory",
            execution_backend="immediate",
            worker=WorkerConfig(placement="external"),
        )
    )
    await queue_svc.open()
    try:
        bg = QueuedBackgroundTask(
            send_team_invitation_email_task,
            service=queue_svc,
            invitee_email="guest@example.com",
            inviter_name="Owner",
            team_name="Core",
            invitation_url="https://app.example.com/invite/1",
        )
        assert bg.args[0] is send_team_invitation_email_task
        await bg()
    finally:
        await queue_svc.close()
    assert len(InMemoryBackend.outbox) == 1
    assert InMemoryBackend.outbox[0].to == ["guest@example.com"]
