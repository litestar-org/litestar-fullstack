"""Integration tests for ``LitestarMCP`` JSON-RPC authentication, catalog allowlist, and tool execution."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from litestar_mcp import validate_tool_descriptions
from sqlalchemy import select

from app.db import models as m
from tests.integration.conftest import login_session_client, reset_client_session

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [pytest.mark.anyio, pytest.mark.integration, pytest.mark.endpoints]

_MCP_PROTOCOL_VERSION = "2026-07-28"
_MCP_META: dict[str, Any] = {
    "io.modelcontextprotocol/protocolVersion": _MCP_PROTOCOL_VERSION,
    "io.modelcontextprotocol/clientCapabilities": {},
}


def _mcp_headers(api_key_headers: dict[str, str], method: str, name: str | None = None) -> dict[str, str]:
    """Compose API-key auth and MCP protocol headers for JSON-RPC requests."""
    headers = {
        **api_key_headers,
        "MCP-Protocol-Version": _MCP_PROTOCOL_VERSION,
        "Mcp-Method": method,
    }
    if name is not None:
        headers["Mcp-Name"] = name
    return headers


async def test_mcp_fails_closed_without_api_key_and_rejects_cookie_session(
    client: AsyncClient,
    test_user: m.User,
) -> None:
    """``POST /mcp`` rejects both unauthenticated and cookie-session-only requests with 401."""
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {"_meta": _MCP_META}}
    assert (await client.post("/mcp", json=payload)).status_code == 401

    csrf = await login_session_client(client, test_user.email, "TestPassword123!")
    assert (await client.post("/mcp", json=payload, headers=csrf)).status_code == 401


async def test_mcp_discover_tools_resources_tool_calls_and_key_revocation(
    client: AsyncClient,
    test_user: m.User,
    test_team: m.Team,
    session: AsyncSession,
) -> None:
    """API-key-authenticated callers can discover, inspect allowlisted tools/resources, and execute safe tools."""
    csrf = await login_session_client(client, test_user.email, "TestPassword123!")
    create_key_resp = await client.post(
        "/api/me/api-keys",
        json={"name": "MCP Integration Key", "scopes": ["read", "write", "mcp"]},
        headers=csrf,
    )
    assert create_key_resp.status_code == 201, create_key_resp.text
    key_id = create_key_resp.json()["id"]
    api_key_secret = create_key_resp.json()["secret"]
    auth_headers = {"Authorization": f"Bearer {api_key_secret}"}

    reset_client_session(client)

    discover_resp = await client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "server/discover", "params": {"_meta": _MCP_META}},
        headers=_mcp_headers(auth_headers, "server/discover"),
    )
    assert discover_resp.status_code == 200, discover_resp.text
    discover_result = discover_resp.json()["result"]
    assert "io.modelcontextprotocol/tasks" in discover_result["capabilities"].get("extensions", {})

    tools_resp = await client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {"_meta": _MCP_META}},
        headers=_mcp_headers(auth_headers, "tools/list"),
    )
    assert tools_resp.status_code == 200, tools_resp.text
    tools = tools_resp.json()["result"]["tools"]
    tool_names = {tool["name"] for tool in tools}
    assert tool_names == {"create_tag", "list_my_tasks", "enqueue_team_report"}
    assert not any("admin" in name.lower() or "delete" in name.lower() for name in tool_names)
    assert validate_tool_descriptions(tools) == []

    resources_resp = await client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 3, "method": "resources/list", "params": {"_meta": _MCP_META}},
        headers=_mcp_headers(auth_headers, "resources/list"),
    )
    assert resources_resp.status_code == 200, resources_resp.text
    resources = resources_resp.json()["result"]["resources"]
    resource_names = {item["name"] for item in resources}
    assert {"system_health", "user_profile", "teams_list", "tags_catalog"}.issubset(resource_names)
    assert not any("admin" in name.lower() for name in resource_names)

    health_resource = next(item for item in resources if item["name"] == "system_health")
    read_resp = await client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 4,
            "method": "resources/read",
            "params": {"uri": health_resource["uri"], "_meta": _MCP_META},
        },
        headers=_mcp_headers(auth_headers, "resources/read", health_resource["uri"]),
    )
    assert read_resp.status_code == 200, read_resp.text
    assert "error" not in read_resp.json()

    call_tag_resp = await client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "create_tag",
                "arguments": {"data": {"name": "pg-mcp-tag"}},
                "_meta": _MCP_META,
            },
        },
        headers=_mcp_headers(auth_headers, "tools/call", "create_tag"),
    )
    assert call_tag_resp.status_code == 200, call_tag_resp.text
    assert "error" not in call_tag_resp.json()

    call_report_resp = await client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "enqueue_team_report",
                "arguments": {"team_id": str(test_team.id)},
                "_meta": _MCP_META,
            },
        },
        headers=_mcp_headers(auth_headers, "tools/call", "enqueue_team_report"),
    )
    assert call_report_resp.status_code == 200, call_report_resp.text
    assert "error" not in call_report_resp.json()

    audit_rows = (
        await session.scalars(select(m.AuditLog).where(m.AuditLog.action.like("security.mcp.tool.call.%")))
    ).all()
    assert any(row.action == "security.mcp.tool.call.completed" for row in audit_rows)
    for row in audit_rows:
        assert api_key_secret not in str(row.details)

    csrf = await login_session_client(client, test_user.email, "TestPassword123!")
    revoke_resp = await client.delete(f"/api/me/api-keys/{key_id}", headers=csrf)
    assert revoke_resp.status_code == 204

    reset_client_session(client)
    revoked_resp = await client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 7, "method": "tools/list", "params": {"_meta": _MCP_META}},
        headers=_mcp_headers(auth_headers, "tools/list"),
    )
    assert revoked_resp.status_code == 401
