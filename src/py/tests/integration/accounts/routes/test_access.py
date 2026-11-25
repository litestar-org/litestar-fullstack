"""PostgreSQL integration tests for LocalAuth.session, CSRF protection, and session lifecycle."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select

from app.db import models as m
from tests.integration.conftest import CSRF_HEADER_NAME, fetch_csrf_headers, login_session_client

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [pytest.mark.anyio, pytest.mark.integration, pytest.mark.auth]


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
