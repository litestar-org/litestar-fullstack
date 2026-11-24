"""Unit/HTTP tests for Admin SecureControllers, DashboardQueryService, AuditLogService, and AdminQueueController."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import uuid4

import pytest
from advanced_alchemy.base import orm_registry
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar import Litestar, get
from litestar.testing import AsyncTestClient
from litestar_queues import QueueConfig, QueuePlugin, QueueService, WorkerConfig
from litestar_security import CSRF_REQUIRED_OPT_KEY, SecurityPlugin, public
from litestar_security.accounts import Argon2PasswordHasher

from app.db import models as m
from app.domain.accounts.security import (
    build_csrf_config,
    build_security_config,
    build_session_middleware,
    build_session_store,
)
from app.domain.admin.controllers import (
    AdminQueueController,
    AdminTeamsController,
    AdminUsersController,
    AuditController,
    DashboardController,
)
from app.domain.admin.services import AuditLogService, DashboardQueryService
from app.domain.system.jobs import scheduler_canary
from app.lib.settings import AppSettings, DatabaseSettings, SecuritySettings, Settings

if TYPE_CHECKING:
    from pathlib import Path

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

pytestmark = pytest.mark.anyio


async def _build_admin_app(tmp_path: Path, name: str) -> tuple[Litestar, SQLAlchemyAsyncConfig]:
    db_cfg = DatabaseSettings(URL=f"sqlite+aiosqlite:///{tmp_path / name}").get_config()
    async with db_cfg.get_engine().begin() as conn:
        await conn.run_sync(orm_registry.metadata.create_all)

    settings = Settings(
        app=AppSettings(SECRET_KEY="admin-test-secret", COOKIE_SECURE=False),
        security=SecuritySettings(COOKIE_SECURE=False),
    )

    @get("/api/csrf", opt={"auth": public(), CSRF_REQUIRED_OPT_KEY: True})
    async def csrf_bootstrap() -> dict[str, bool]:
        return {"ok": True}

    sec_cfg = build_security_config(settings, db_cfg)
    queue_cfg = QueueConfig(
        queue_backend="memory",
        execution_backend="local",
        worker=WorkerConfig(placement="external"),
    )
    app = Litestar(
        route_handlers=[
            csrf_bootstrap,
            DashboardController,
            AdminUsersController,
            AdminTeamsController,
            AuditController,
            AdminQueueController,
        ],
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


async def _seed_user(
    db_cfg: SQLAlchemyAsyncConfig,
    *,
    email: str,
    is_superuser: bool = False,
    with_mfa: bool = False,
) -> m.User:
    hashed = await Argon2PasswordHasher().hash("StrongPassword!123")
    async with db_cfg.get_session() as session:
        user = m.User(
            email=email,
            name="Admin Test User",
            hashed_password=hashed,
            is_active=True,
            is_verified=True,
            is_superuser=is_superuser,
        )
        session.add(user)
        await session.flush()
        if with_mfa:
            session.add(
                m.UserMFAFactor(
                    user_id=user.id,
                    method_id=f"totp-{user.id}",
                    secret_ciphertext=b"enc",
                    key_version="v1",
                    is_confirmed=True,
                )
            )
        await session.commit()
        await session.refresh(user)
        return user


async def _login(client: AsyncTestClient[Any], email: str) -> str:
    boot = await client.get("/api/csrf")
    assert boot.status_code == 200
    csrf = client.cookies.get("XSRF-TOKEN") or ""
    resp = await client.post(
        "/api/access/login",
        json={"identifier": email, "password": "StrongPassword!123"},
        headers={"X-XSRF-TOKEN": csrf},
    )
    assert resp.status_code in {200, 201, 204}, resp.text
    return client.cookies.get("XSRF-TOKEN") or csrf


async def test_admin_guards_dashboard_query_service_users_and_queues(tmp_path: Path) -> None:
    app, db_cfg = await _build_admin_app(tmp_path, "admin.sqlite3")
    admin = await _seed_user(db_cfg, email="root@example.com", is_superuser=True)
    member = await _seed_user(db_cfg, email="regular@example.com", is_superuser=False, with_mfa=False)
    mfa_user = await _seed_user(db_cfg, email="mfa-user@example.com", is_superuser=False, with_mfa=True)

    async with db_cfg.get_session() as session:
        session.add(m.Team(name="Ops", slug="ops"))
        await session.commit()

    async with AuditLogService.new(config=db_cfg) as audit_svc:
        await audit_svc.log_action(action="user.login", actor_id=admin.id, actor_email=admin.email)
        recent = await audit_svc.get_user_activity(admin.id)
        assert len(recent) == 1

    async with DashboardQueryService.new(config=db_cfg) as query_svc:
        stats = await query_svc.get_stats()
        assert stats.total_users == 3
        assert stats.active_users == 3
        assert stats.verified_users == 3
        assert stats.total_teams == 1
        assert stats.events_today >= 1

    async with AsyncTestClient(app=app) as user_client:
        await _login(user_client, member.email)
        assert (await user_client.get("/api/admin/dashboard/stats")).status_code == 403
        assert (await user_client.get("/api/admin/users/")).status_code == 403
        assert (await user_client.get("/api/admin/queues/tasks")).status_code == 403
        assert (await user_client.get("/api/admin/audit/")).status_code == 403

    async with AsyncTestClient(app=app) as admin_client:
        csrf = await _login(admin_client, admin.email)

        dash_resp = await admin_client.get("/api/admin/dashboard/stats")
        assert dash_resp.status_code == 200
        assert dash_resp.json()["totalUsers"] == 3
        assert dash_resp.json()["totalTeams"] == 1

        detail_resp = await admin_client.get(f"/api/admin/users/{mfa_user.id}")
        assert detail_resp.status_code == 200
        detail_body = detail_resp.json()
        assert detail_body["hasPassword"] is True
        assert detail_body["isTwoFactorEnabled"] is True

        self_del = await admin_client.delete(
            f"/api/admin/users/{admin.id}",
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert self_del.status_code == 403

        queue_svc: QueueService = app.plugins.get(QueuePlugin).get_service()
        enqueued = await queue_svc.enqueue(scheduler_canary)

        list_resp = await admin_client.get("/api/admin/queues/tasks")
        assert list_resp.status_code == 200
        list_body = list_resp.json()
        assert list_body["total"] >= 1
        assert any(item["taskId"] == str(enqueued.id) for item in list_body["items"])

        cancel_resp = await admin_client.post(
            f"/api/admin/queues/tasks/{enqueued.id}/cancel",
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert cancel_resp.status_code in {200, 201}, cancel_resp.text
        assert cancel_resp.json()["cancelled"] is True

        missing_cancel = await admin_client.post(
            f"/api/admin/queues/tasks/{uuid4()}/cancel",
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert missing_cancel.status_code == 404
