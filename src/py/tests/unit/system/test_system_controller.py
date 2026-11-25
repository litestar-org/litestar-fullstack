"""Unit/HTTP tests for SystemController (/health, /api/config/auth) and UserQueueController."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from advanced_alchemy.base import orm_registry
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar import Litestar
from litestar.testing import AsyncTestClient
from litestar_queues import QueueConfig, QueuePlugin, QueueService, WorkerConfig
from litestar_security import SecurityPlugin
from litestar_security.accounts import Argon2PasswordHasher
from sqlalchemy.exc import OperationalError

from app.db import models as m
from app.domain.accounts.security import (
    build_csrf_config,
    build_security_config,
    build_session_middleware,
    build_session_store,
)
from app.domain.system.controllers import SystemController, UserQueueController
from app.domain.system.jobs import export_team_summary
from app.lib.settings import AppSettings, DatabaseSettings, SecuritySettings, Settings

if TYPE_CHECKING:
    from pathlib import Path

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

pytestmark = pytest.mark.anyio


async def _build_system_app(tmp_path: Path, name: str) -> tuple[Litestar, SQLAlchemyAsyncConfig]:
    db_cfg = DatabaseSettings(URL=f"sqlite+aiosqlite:///{tmp_path / name}").get_config()
    async with db_cfg.get_engine().begin() as conn:
        await conn.run_sync(orm_registry.metadata.create_all)

    settings = Settings(
        app=AppSettings(SECRET_KEY="system-test-secret", COOKIE_SECURE=False),
        security=SecuritySettings(COOKIE_SECURE=False),
    )
    sec_cfg = build_security_config(settings, db_cfg)
    queue_cfg = QueueConfig(
        queue_backend="memory",
        execution_backend="local",
        worker=WorkerConfig(placement="external"),
    )
    app = Litestar(
        route_handlers=[SystemController, UserQueueController],
        plugins=[
            SQLAlchemyPlugin(config=db_cfg),
            QueuePlugin(config=queue_cfg),
            SecurityPlugin(sec_cfg),
        ],
        middleware=[build_session_middleware(settings)],
        csrf_config=build_csrf_config(settings),
        stores={"sessions": build_session_store(db_cfg)},
    )
    return app, db_cfg


async def _seed_user(db_cfg: SQLAlchemyAsyncConfig, *, email: str) -> m.User:
    hashed = await Argon2PasswordHasher().hash("StrongPassword!123")
    async with db_cfg.get_session() as session:
        user = m.User(email=email, name="Sys User", hashed_password=hashed, is_active=True, is_verified=True)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def test_health_auth_config_and_user_queue_isolation(tmp_path: Path) -> None:
    app, db_cfg = await _build_system_app(tmp_path, "system.sqlite3")
    alice = await _seed_user(db_cfg, email="alice@example.com")
    bob = await _seed_user(db_cfg, email="bob@example.com")

    async with db_cfg.get_session() as session:
        team = m.Team(name="Platform", slug="platform")
        session.add(team)
        await session.flush()
        session.add(m.TeamMember(team_id=team.id, user_id=alice.id, role=m.TeamRoles.MEMBER, is_owner=False))
        await session.commit()
        team_id = str(team.id)

    async with AsyncTestClient(app=app) as client:
        health_resp = await client.get("/health")
        assert health_resp.status_code == 200
        body = health_resp.json()
        assert body["databaseStatus"] == "online"
        assert body["queueStatus"] == "online"

        cfg_resp = await client.get("/api/config/auth")
        assert cfg_resp.status_code == 200
        cfg_body = cfg_resp.json()
        assert set(cfg_body) == {"githubEnabled", "passkeysEnabled", "mfaEnabled", "emailVerificationRequired"}
        assert cfg_body["emailVerificationRequired"] is True
        assert cfg_body["passkeysEnabled"] is True
        assert cfg_body["mfaEnabled"] is True
        assert "XSRF-TOKEN" in client.cookies

        csrf = client.cookies["XSRF-TOKEN"]
        login = await client.post(
            "/api/access/login",
            json={"identifier": alice.email, "password": "StrongPassword!123"},
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert login.status_code in {200, 201, 204}
        csrf = client.cookies.get("XSRF-TOKEN") or csrf

        enq_resp = await client.post(
            f"/api/queues/reports/team-summary/{team_id}",
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert enq_resp.status_code == 201, enq_resp.text
        task_id = enq_resp.json()["taskId"]

        queue_svc: QueueService = app.plugins.get(QueuePlugin).get_service()
        await queue_svc.enqueue(
            export_team_summary,
            team_id=team_id,
            requested_by_id=str(bob.id),
            metadata={"requested_by_id": str(bob.id)},
        )

        alice_tasks = await client.get("/api/queues/tasks")
        assert alice_tasks.status_code == 200
        ids = [item["taskId"] for item in alice_tasks.json()["items"]]
        assert ids == [task_id]

    async with AsyncTestClient(app=app) as bob_client:
        await bob_client.get("/api/config/auth")
        csrf = bob_client.cookies["XSRF-TOKEN"]
        assert (
            await bob_client.post(
                "/api/access/login",
                json={"identifier": bob.email, "password": "StrongPassword!123"},
                headers={"X-XSRF-TOKEN": csrf},
            )
        ).status_code in {200, 201, 204}
        csrf = bob_client.cookies.get("XSRF-TOKEN") or csrf
        denied = await bob_client.post(
            f"/api/queues/reports/team-summary/{team_id}",
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert denied.status_code == 403


async def test_health_returns_503_when_queue_or_db_offline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, _db_cfg = await _build_system_app(tmp_path, "system_degraded.sqlite3")

    async def _fail_queue(*_args: Any, **_kwargs: Any) -> Any:
        msg = "queue unavailable"
        raise RuntimeError(msg)

    monkeypatch.setattr(QueueService, "list_tasks", _fail_queue)
    async with AsyncTestClient(app=app) as degraded_client:
        resp = await degraded_client.get("/health")
        assert resp.status_code == 503
        assert resp.json()["databaseStatus"] == "online"
        assert resp.json()["queueStatus"] == "offline"

    monkeypatch.undo()

    from sqlalchemy.ext.asyncio import AsyncSession

    original_execute = AsyncSession.execute

    async def _fail_db(self: AsyncSession, statement: Any, *args: Any, **kwargs: Any) -> Any:
        if "select 1" in str(statement).lower():
            stmt = "select 1"
            err = Exception("db down")
            raise OperationalError(stmt, {}, err)
        return await original_execute(self, statement, *args, **kwargs)

    monkeypatch.setattr(AsyncSession, "execute", _fail_db)
    async with AsyncTestClient(app=app) as db_down_client:
        resp = await db_down_client.get("/health")
        assert resp.status_code == 503
        assert resp.json()["databaseStatus"] == "offline"
