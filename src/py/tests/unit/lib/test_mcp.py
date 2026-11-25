"""Unit/HTTP tests for LitestarMCP API-key auth, discovery, catalog allowlist, audit hooks, and strict bounds."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from advanced_alchemy.base import orm_registry
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar import Litestar
from litestar.testing import AsyncTestClient
from litestar_mcp import LitestarMCP, validate_tool_descriptions
from litestar_queues import QueueConfig, QueuePlugin, WorkerConfig
from litestar_security import SecurityPlugin, required
from litestar_security.accounts import Argon2PasswordHasher
from litestar_security.context import CredentialRestrictions
from sqlalchemy import select

from app.db import models as m
from app.domain.accounts.controllers import ProfileController
from app.domain.accounts.security import (
    AuditSecurityEventSink,
    SQLAlchemyAPIKeyStore,
    build_api_key_service,
    build_csrf_config,
    build_security_config,
    build_session_middleware,
    build_session_store,
    require_application_access,
)
from app.domain.admin.controllers import AdminQueueController, AdminUsersController, DashboardController
from app.domain.system.controllers import SystemController, UserQueueController
from app.domain.tags.controllers import TagController
from app.domain.teams.controllers import TeamController
from app.lib.secrets import API_KEY_PEPPER_INFO, derive_subkey
from app.lib.settings import AppSettings, DatabaseSettings, MCPSettings, SecuritySettings, Settings
from app.server.core import build_mcp_audit_hooks
from tests.factories import grant_application_access

if TYPE_CHECKING:
    from pathlib import Path

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

pytestmark = pytest.mark.anyio


async def _build_mcp_app(
    tmp_path: Path,
    name: str,
    *,
    sink: AuditSecurityEventSink | None = None,
) -> tuple[Litestar, SQLAlchemyAsyncConfig, Settings]:
    db_cfg = DatabaseSettings(URL=f"sqlite+aiosqlite:///{tmp_path / name}").get_config()
    async with db_cfg.get_engine().begin() as conn:
        await conn.run_sync(orm_registry.metadata.create_all)

    settings = Settings(
        app=AppSettings(SECRET_KEY="mcp-test-secret", COOKIE_SECURE=False),
        security=SecuritySettings(COOKIE_SECURE=False),
        mcp=MCPSettings(),
    )
    sec_cfg = build_security_config(settings, db_cfg)
    queue_cfg = QueueConfig(
        queue_backend="memory",
        execution_backend="local",
        worker=WorkerConfig(placement="external"),
    )
    before_hook, after_hook = build_mcp_audit_hooks(sink or AuditSecurityEventSink(db_cfg))
    mcp_cfg = settings.mcp.get_config(
        auth=required("api-key"),
        before_tool_call=before_hook,
        after_tool_call=after_hook,
    )
    app = Litestar(
        route_handlers=[
            SystemController,
            ProfileController,
            TeamController,
            TagController,
            UserQueueController,
            AdminUsersController,
            AdminQueueController,
            DashboardController,
        ],
        plugins=[
            SQLAlchemyPlugin(config=db_cfg),
            QueuePlugin(config=queue_cfg),
            LitestarMCP(config=mcp_cfg),
            SecurityPlugin(sec_cfg),
        ],
        middleware=[build_session_middleware(settings)],
        csrf_config=build_csrf_config(settings),
        stores={"sessions": build_session_store(db_cfg)},
        guards=[require_application_access],
    )
    return app, db_cfg, settings


async def _seed_user(db_cfg: SQLAlchemyAsyncConfig, *, email: str) -> m.User:
    hashed = await Argon2PasswordHasher().hash("StrongPassword!123")
    async with db_cfg.get_session() as session:
        user = m.User(email=email, name="MCP User", hashed_password=hashed, is_active=True, is_verified=True)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        await grant_application_access(session, user)
        return user


async def test_mcp_auth_catalog_openapi_isolation_audit_and_bounds(tmp_path: Path) -> None:
    app, db_cfg, settings = await _build_mcp_app(tmp_path, "mcp.sqlite3")
    user = await _seed_user(db_cfg, email="mcp-user@example.com")

    key_svc = build_api_key_service(
        SQLAlchemyAPIKeyStore(db_cfg),
        derive_subkey(settings.app.SECRET_KEY, API_KEY_PEPPER_INFO),
    )
    issued = await key_svc.issue(
        subject_id=str(user.id),
        restrictions=CredentialRestrictions(scopes=frozenset({"read", "write", "mcp"})),
    )

    openapi_paths = set((app.openapi_schema.to_schema().get("paths") or {}).keys())
    assert "/mcp" not in openapi_paths

    async with AsyncTestClient(app=app) as client:
        unauth = await client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        assert unauth.status_code == 401

        await client.get("/api/config/auth")
        csrf = client.cookies["XSRF-TOKEN"]
        login = await client.post(
            "/api/access/login",
            json={"identifier": user.email, "password": "StrongPassword!123"},
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert login.status_code in {200, 201, 204}
        csrf = client.cookies.get("XSRF-TOKEN") or csrf
        session_only = await client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert session_only.status_code == 401

    base_headers = {
        "Authorization": f"Bearer {issued.value}",
        "MCP-Protocol-Version": "2026-07-28",
    }
    meta = {
        "io.modelcontextprotocol/protocolVersion": "2026-07-28",
        "io.modelcontextprotocol/clientCapabilities": {},
    }
    async with AsyncTestClient(app=app) as mcp_client:
        discover_resp = await mcp_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 10,
                "method": "server/discover",
                "params": {"_meta": meta},
            },
            headers={**base_headers, "Mcp-Method": "server/discover"},
        )
        assert discover_resp.status_code == 200, discover_resp.text
        discover_result = discover_resp.json()["result"]
        server_info = discover_result.get("_meta", {}).get("io.modelcontextprotocol/serverInfo", {})
        assert server_info.get("name") == settings.mcp.NAME
        assert "io.modelcontextprotocol/tasks" in discover_result["capabilities"].get("extensions", {})

        tools_resp = await mcp_client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 11, "method": "tools/list", "params": {"_meta": meta}},
            headers={**base_headers, "Mcp-Method": "tools/list"},
        )
        assert tools_resp.status_code == 200, tools_resp.text
        tools = tools_resp.json()["result"]["tools"]
        tool_names = {tool["name"] for tool in tools}
        assert tool_names == {"create_tag", "list_my_tasks", "enqueue_team_report"}
        assert validate_tool_descriptions(tools) == []

        resources_resp = await mcp_client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 12, "method": "resources/list", "params": {"_meta": meta}},
            headers={**base_headers, "Mcp-Method": "resources/list"},
        )
        assert resources_resp.status_code == 200, resources_resp.text
        resource_names = {r["name"] for r in resources_resp.json()["result"]["resources"]}
        assert {"system_health", "user_profile", "teams_list", "tags_catalog"}.issubset(resource_names)

        templates_resp = await mcp_client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 13, "method": "resources/templates/list", "params": {"_meta": meta}},
            headers={**base_headers, "Mcp-Method": "resources/templates/list"},
        )
        assert templates_resp.status_code == 200, templates_resp.text
        template_uris = {t["uriTemplate"] for t in templates_resp.json()["result"]["resourceTemplates"]}
        assert "app://teams/{team_id}" in template_uris

        call_resp = await mcp_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 14,
                "method": "tools/call",
                "params": {"name": "create_tag", "arguments": {"data": {"name": "mcp-created"}}, "_meta": meta},
            },
            headers={**base_headers, "Mcp-Method": "tools/call", "Mcp-Name": "create_tag"},
        )
        assert call_resp.status_code == 200, call_resp.text
        assert "error" not in call_resp.json()

    async with db_cfg.get_session() as session:
        audit_rows = (
            await session.scalars(select(m.AuditLog).where(m.AuditLog.action.like("security.mcp.tool.call.%")))
        ).all()
        actions = {row.action for row in audit_rows}
        assert "security.mcp.tool.call.started" in actions
        assert "security.mcp.tool.call.completed" in actions
        assert len({(row.details or {})["correlation"]["correlation_id"] for row in audit_rows}) == 1
        for row in audit_rows:
            assert issued.value not in str(row.details)


async def test_mcp_audit_hook_errors_are_swallowed(tmp_path: Path) -> None:
    class _BrokenSink(AuditSecurityEventSink):
        async def emit(self, event: Any) -> None:
            _ = event
            msg = "sink exploded"
            raise RuntimeError(msg)

    unused_db = DatabaseSettings(URL=f"sqlite+aiosqlite:///{tmp_path / 'unused.sqlite3'}").get_config()
    app, db_cfg, settings = await _build_mcp_app(tmp_path, "mcp_broken_sink.sqlite3", sink=_BrokenSink(unused_db))
    user = await _seed_user(db_cfg, email="mcp-broken@example.com")
    issued = await build_api_key_service(
        SQLAlchemyAPIKeyStore(db_cfg),
        derive_subkey(settings.app.SECRET_KEY, API_KEY_PEPPER_INFO),
    ).issue(
        subject_id=str(user.id),
        restrictions=CredentialRestrictions(scopes=frozenset({"read", "write", "mcp"})),
    )
    async with AsyncTestClient(app=app) as client:
        resp = await client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 20,
                "method": "tools/call",
                "params": {"name": "create_tag", "arguments": {"data": {"name": "still-works"}}},
            },
            headers={"Authorization": f"Bearer {issued.value}"},
        )
        assert resp.status_code == 200, resp.text
        assert "error" not in resp.json()


def test_application_core_respects_mcp_enabled_false(monkeypatch: pytest.MonkeyPatch) -> None:
    from litestar_autowire import AutowireConfig

    from app.lib.settings import get_settings
    from app.server.core import ApplicationCore

    settings = get_settings()
    monkeypatch.setattr(settings.mcp, "ENABLED", False)
    app = Litestar(
        plugins=[
            ApplicationCore(
                autowire_config=AutowireConfig(domain_packages=[], integrations=[]),
                queue_config=QueueConfig(
                    queue_backend="memory",
                    execution_backend="local",
                    worker=WorkerConfig(placement="external"),
                ),
            )
        ]
    )
    with pytest.raises(KeyError):
        app.plugins.get(LitestarMCP)
    assert not any(route.path.startswith("/mcp") for route in app.routes)
