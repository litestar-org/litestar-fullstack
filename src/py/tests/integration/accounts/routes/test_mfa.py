"""PostgreSQL integration tests for TOTP MFA enrollment, login challenge, replay protection, and removal."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlparse

import pyotp
import pytest

from tests.integration.conftest import fetch_csrf_headers, login_session_client, reset_client_session

if TYPE_CHECKING:
    from httpx import AsyncClient

    from app.db import models as m

pytestmark = [pytest.mark.anyio, pytest.mark.integration, pytest.mark.auth, pytest.mark.security]


async def test_totp_enrollment_login_challenge_replay_and_removal(
    client: AsyncClient,
    test_user: m.User,
) -> None:
    """Enroll TOTP, confirm code, enforce login challenge with single-use replay rejection, and remove factor."""
    csrf = await login_session_client(client, test_user.email, "TestPassword123!")

    step_up_enroll = await client.post(
        "/api/access/step-up/totp-enroll",
        json={"method": "password", "credential": "TestPassword123!"},
        headers=csrf,
    )
    assert step_up_enroll.status_code == 200, step_up_enroll.text
    enroll_grant = step_up_enroll.json()["grant"]

    enroll_res = await client.post(
        "/api/access/mfa/totp/enroll",
        json={"label": "Test Authenticator", "step_up_grant": enroll_grant},
        headers=csrf,
    )
    assert enroll_res.status_code in {200, 201}, enroll_res.text
    provisioned = enroll_res.json()
    method_id = provisioned["method_id"]
    enrollment_id = provisioned["enrollment_id"]
    secret = parse_qs(urlparse(provisioned["provisioning_uri"]).query)["secret"][0]

    code = pyotp.TOTP(secret).now()
    confirm_res = await client.post(
        "/api/access/mfa/totp/verify",
        json={"enrollment_id": enrollment_id, "code": code},
        headers=csrf,
    )
    assert confirm_res.status_code == 200, confirm_res.text
    recovery_codes = confirm_res.json()["codes"]
    assert len(recovery_codes) >= 8

    profile_res = await client.get("/api/me")
    assert profile_res.status_code == 200
    assert profile_res.json()["isTwoFactorEnabled"] is True
    assert profile_res.json()["totpMethodId"] == method_id

    reset_client_session(client)
    fresh_csrf = await fetch_csrf_headers(client)
    login_res = await client.post(
        "/api/access/login",
        json={"identifier": test_user.email, "password": "TestPassword123!"},
        headers=fresh_csrf,
    )
    assert login_res.status_code == 403, login_res.text
    challenge_payload = login_res.json()
    assert challenge_payload["account_id"] == str(test_user.id)
    challenge = challenge_payload["challenge"]

    complete_res = await client.post(
        "/api/access/login/mfa",
        json={
            "account_id": str(test_user.id),
            "challenge": challenge,
            "method": "recovery-code",
            "code": recovery_codes[0],
        },
        headers=fresh_csrf,
    )
    assert complete_res.status_code == 200, complete_res.text

    replay_res = await client.post(
        "/api/access/login/mfa",
        json={
            "account_id": str(test_user.id),
            "challenge": challenge,
            "method": "recovery-code",
            "code": recovery_codes[1],
        },
        headers=fresh_csrf,
    )
    assert replay_res.status_code in {400, 401}

    promoted_me = await client.get("/api/me")
    assert promoted_me.status_code == 200
    assert promoted_me.json()["email"] == test_user.email

    promoted_csrf = await fetch_csrf_headers(client)
    step_up_remove = await client.post(
        "/api/access/step-up/totp-remove",
        json={"method": "password", "credential": "TestPassword123!"},
        headers=promoted_csrf,
    )
    assert step_up_remove.status_code == 200, step_up_remove.text
    remove_res = await client.post(
        f"/api/access/mfa/totp/{method_id}/remove",
        json={"step_up_grant": step_up_remove.json()["grant"]},
        headers=promoted_csrf,
    )
    assert remove_res.status_code == 200, remove_res.text

    profile_after = await client.get("/api/me")
    assert profile_after.status_code == 200
    assert profile_after.json()["isTwoFactorEnabled"] is False
    assert profile_after.json()["totpMethodId"] is None
