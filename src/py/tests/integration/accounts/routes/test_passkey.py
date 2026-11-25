"""PostgreSQL integration tests for WebAuthn Passkey registration options, listing, and error rejection."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from tests.integration.conftest import fetch_csrf_headers, reset_client_session

if TYPE_CHECKING:
    from httpx import AsyncClient

    from app.db import models as m

pytestmark = [pytest.mark.anyio, pytest.mark.integration, pytest.mark.auth, pytest.mark.security]


async def test_passkey_registration_options_list_and_invalid_assertion_rejected(
    authenticated_client: AsyncClient,
    client: AsyncClient,
    test_user: m.User,
) -> None:
    """Passkey options require step-up, empty list returns cleanly, and malformed assertions fail closed."""
    list_res = await authenticated_client.get("/api/access/passkeys")
    assert list_res.status_code == 200
    assert list_res.json() == []

    step_up = await authenticated_client.post(
        "/api/access/step-up/passkey-register",
        json={"method": "password", "credential": "TestPassword123!"},
    )
    assert step_up.status_code == 200, step_up.text

    options_res = await authenticated_client.post(
        "/api/access/passkeys/registration/options",
        json={"step_up_grant": step_up.json()["grant"], "user_name": test_user.email},
    )
    assert options_res.status_code == 200, options_res.text
    parsed_options = json.loads(options_res.json()["options"])
    assert "challenge" in parsed_options

    bad_reg = await authenticated_client.post(
        "/api/access/passkeys/registration/verify",
        json={"account_id": str(test_user.id), "response": "{}"},
    )
    assert bad_reg.status_code in {400, 401}

    reset_client_session(client)
    csrf = await fetch_csrf_headers(client)
    auth_opts = await client.post(
        "/api/access/passkeys/authentication/options",
        json={"account_id": str(test_user.id)},
        headers=csrf,
    )
    assert auth_opts.status_code == 200, auth_opts.text
    binding = auth_opts.json()["binding"]
    assert binding

    bad_assert = await client.post(
        "/api/access/passkeys/authentication/verify",
        json={"account_id": str(test_user.id), "binding": binding, "response": "{}"},
        headers=csrf,
    )
    assert bad_assert.status_code in {400, 401}
