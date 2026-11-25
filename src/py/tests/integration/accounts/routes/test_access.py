"""PostgreSQL integration tests for LocalAuth.session, CSRF protection, and session lifecycle."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest
from litestar_security.accounts import Argon2PasswordHasher
from sqlalchemy import delete, select

from app.db import models as m
from app.domain.accounts.security import APPLICATION_ACCESS_REQUIRED
from tests.integration.conftest import (
    CSRF_HEADER_NAME,
    fetch_csrf_headers,
    login_session_client,
    reset_client_session,
)

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [pytest.mark.anyio, pytest.mark.integration, pytest.mark.auth]

PASSWORD = "TestPassword123!"


async def _create_user_without_application_access(
    session: AsyncSession,
    email: str,
    *,
    is_superuser: bool = False,
) -> m.User:
    user = m.User(
        email=email,
        hashed_password=await Argon2PasswordHasher().hash(PASSWORD),
        is_active=True,
        is_verified=True,
        is_superuser=is_superuser,
    )
    session.add(user)
    await session.commit()
    return user


async def test_registration_login_csrf_and_logout_lifecycle(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Register -> enqueue verification email -> login with cookie -> enforce CSRF -> logout."""
    csrf = await fetch_csrf_headers(client)

    register_res = await client.post(
        "/api/access/register",
        json={
            "identifier": "alice.session@example.com",
            "password": "StrongPassword!123",
            "display_name": "Alice Session",
        },
        headers=csrf,
    )
    assert register_res.status_code in {200, 201, 202}, register_res.text

    user = await session.scalar(select(m.User).where(m.User.email == "alice.session@example.com"))
    assert user is not None

    verify_task = await session.scalar(
        select(m.QueueTask)
        .where(m.QueueTask.task_name == "email.send_verification")
        .order_by(m.QueueTask.created_at.desc())
    )
    assert verify_task is not None
    verify_token = (verify_task.kwargs_json or {}).get("token")
    assert isinstance(verify_token, str)
    assert verify_token

    confirm_res = await client.post(
        "/api/access/verification/confirm",
        json={"token": verify_token},
        headers=csrf,
    )
    assert confirm_res.status_code in {200, 204}, confirm_res.text

    login_res = await client.post(
        "/api/access/login",
        json={"identifier": "alice.session@example.com", "password": "StrongPassword!123"},
        headers=csrf,
    )
    assert login_res.status_code == 200, login_res.text
    set_cookie = login_res.headers.get("set-cookie", "")
    assert "HttpOnly" in set_cookie or "httponly" in set_cookie.lower()

    profile_res = await client.get("/api/me")
    assert profile_res.status_code == 200
    assert profile_res.json()["email"] == "alice.session@example.com"

    no_csrf_patch = await client.patch(
        "/api/me",
        json={"name": "Blocked Without CSRF"},
        headers={CSRF_HEADER_NAME: ""},
    )
    assert no_csrf_patch.status_code == 403

    csrf_after_login = await fetch_csrf_headers(client)
    valid_patch = await client.patch(
        "/api/me",
        json={"name": "Alice Updated"},
        headers=csrf_after_login,
    )
    assert valid_patch.status_code == 200
    assert valid_patch.json()["name"] == "Alice Updated"

    logout_res = await client.post("/api/access/logout", headers=csrf_after_login)
    assert logout_res.status_code in {200, 204}

    after_logout = await client.get("/api/me")
    assert after_logout.status_code == 401


async def test_unauthenticated_and_inactive_login_fail_closed(
    client: AsyncClient,
    inactive_user: m.User,
) -> None:
    """Protected routes reject unauthenticated callers and inactive accounts cannot log in."""
    me_res = await client.get("/api/me")
    assert me_res.status_code == 401

    csrf = await fetch_csrf_headers(client)
    bad_login = await client.post(
        "/api/access/login",
        json={"identifier": inactive_user.email, "password": "TestPassword123!"},
        headers=csrf,
    )
    assert bad_login.status_code == 401


async def test_email_verification_and_password_recovery_endpoints(
    client: AsyncClient,
    test_user: m.User,
    unverified_user: m.User,
) -> None:
    """Verification resend and password recovery accept valid identifiers without leaking tokens."""
    csrf = await fetch_csrf_headers(client)
    resend = await client.post(
        "/api/access/verification",
        json={"identifier": unverified_user.email},
        headers=csrf,
    )
    assert resend.status_code in {200, 202}

    recovery = await client.post(
        "/api/access/password/recovery",
        json={"identifier": test_user.email},
        headers=csrf,
    )
    assert recovery.status_code in {200, 202}
    assert not re.search(r"token[\"']?\s*:", recovery.text)

    headers = await login_session_client(client, test_user.email, "TestPassword123!")
    assert CSRF_HEADER_NAME in headers


async def test_accounts_without_application_access_are_refused_everywhere_but_sign_out(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    await _create_user_without_application_access(session, "no-access@example.com")
    csrf = await login_session_client(client, "no-access@example.com", PASSWORD)

    for path in ("/api/me", "/api/teams", "/api/tags", "/api/me/api-keys", "/api/queues/events/sse/global"):
        refused = await client.get(path)
        assert refused.status_code == 403, path
        assert refused.json()["code"] == APPLICATION_ACCESS_REQUIRED, path

    signed_out = await client.post("/api/access/logout", headers=csrf)
    assert signed_out.status_code in {200, 204}, signed_out.text
    assert (await client.get("/api/me")).status_code == 401


async def test_api_keys_stop_reaching_mcp_when_their_account_loses_application_access(
    client: AsyncClient,
    api_key_headers: dict[str, str],
    test_user: m.User,
    session: AsyncSession,
) -> None:
    reset_client_session(client)
    await session.execute(delete(m.UserRole).where(m.UserRole.user_id == test_user.id))
    await session.commit()

    refused = await client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        headers=api_key_headers,
    )

    assert refused.status_code == 403
    assert refused.json()["code"] == APPLICATION_ACCESS_REQUIRED


async def test_superusers_pass_without_the_application_access_role(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    await _create_user_without_application_access(session, "root@example.com", is_superuser=True)
    await login_session_client(client, "root@example.com", PASSWORD)

    assert (await client.get("/api/me")).status_code == 200
    assert (await client.get("/api/teams")).status_code == 200


async def test_registration_refuses_a_common_password(client: AsyncClient, session: AsyncSession) -> None:
    csrf = await fetch_csrf_headers(client)

    refused = await client.post(
        "/api/access/register",
        json={"identifier": "common.password@example.com", "password": "Password12345"},
        headers=csrf,
    )

    assert refused.status_code == 400, refused.text
    assert await session.scalar(select(m.User).where(m.User.email == "common.password@example.com")) is None
