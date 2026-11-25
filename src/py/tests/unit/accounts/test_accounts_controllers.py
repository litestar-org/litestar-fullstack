"""Unit/HTTP tests for accounts SecureControllers, password re-confirmation, and API key lifecycle."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import pytest
from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar import Litestar, get
from litestar.plugins.problem_details import ProblemDetailsPlugin
from litestar.testing import AsyncTestClient
from litestar_security import CSRF_REQUIRED_OPT_KEY, SecurityPlugin, public
from litestar_security.context import CredentialRestrictions

from app import config as app_config
from app.db import models as m
from app.domain import accounts as accounts_pkg
from app.domain.accounts.controllers import (
    ApiKeyController,
    ProfileController,
    RoleController,
    UserController,
)
from app.domain.accounts.security import (
    APPLICATION_ACCESS_REQUIRED,
    REAUTHENTICATION_REQUIRED,
    SQLAlchemyAPIKeyStore,
    build_api_key_service,
    build_csrf_config,
    build_security_config,
    build_session_middleware,
    build_session_store,
    require_application_access,
)
from app.domain.accounts.services import UserService
from app.lib.settings import AppSettings, DatabaseSettings, SecuritySettings, Settings

if TYPE_CHECKING:
    from pathlib import Path

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

pytestmark = pytest.mark.anyio


async def _build_accounts_app(tmp_path: Path, name: str) -> tuple[Litestar, SQLAlchemyAsyncConfig, list[datetime]]:
    db_cfg = DatabaseSettings(URL=f"sqlite+aiosqlite:///{tmp_path / name}").get_config()
    engine = db_cfg.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(UUIDv7AuditBase.metadata.create_all)

    settings = Settings(
        app=AppSettings(SECRET_KEY="controllers-test-secret", COOKIE_SECURE=False),
        security=SecuritySettings(COOKIE_SECURE=False),
    )

    @get("/api/csrf", opt={"auth": public(), CSRF_REQUIRED_OPT_KEY: True})
    async def csrf_bootstrap() -> dict[str, bool]:
        return {"ok": True}

    clock_box = [datetime.now(UTC)]
    sec_cfg = build_security_config(settings, db_cfg)
    assert sec_cfg.local_auth is not None
    assert sec_cfg.local_auth.session_auth is not None
    sec_cfg.local_auth.session_auth.clock = lambda: clock_box[0]
    app = Litestar(
        route_handlers=[csrf_bootstrap, ProfileController, ApiKeyController, UserController, RoleController],
        plugins=[
            SQLAlchemyPlugin(config=db_cfg),
            ProblemDetailsPlugin(config=app_config.problem_details),
            SecurityPlugin(sec_cfg),
        ],
        guards=[require_application_access],
        middleware=[build_session_middleware(settings)],
        csrf_config=build_csrf_config(settings),
        stores={"sessions": build_session_store(db_cfg)},
    )
    return app, db_cfg, clock_box


async def _seed_user(
    db_cfg: SQLAlchemyAsyncConfig,
    *,
    email: str,
    password: str = "StrongPassword!123",
    name: str = "Test User",
    is_superuser: bool = False,
    application_access: bool = True,
) -> m.User:
    async with UserService.new(config=db_cfg) as users:
        hashed_password = await users.hash_password(password, email=email)
        if application_access:
            user = await users.provision(
                email=email,
                name=name,
                verified=True,
                now=datetime.now(UTC),
                hashed_password=hashed_password,
                is_superuser=is_superuser,
            )
        else:
            user = await users.create(
                m.User(
                    email=email,
                    name=name,
                    hashed_password=hashed_password,
                    is_active=True,
                    is_verified=True,
                    is_superuser=is_superuser,
                )
            )
        await users.repository.session.commit()
        return user


async def _login(client: AsyncTestClient[Any], email: str, password: str = "StrongPassword!123") -> str:
    csrf_token = client.cookies.get("XSRF-TOKEN") or ""
    if not csrf_token:
        boot = await client.get("/api/csrf")
        assert boot.status_code == 200
        csrf_token = client.cookies.get("XSRF-TOKEN") or ""
    login_resp = await client.post(
        "/api/access/login",
        json={"identifier": email, "password": password},
        headers={"X-XSRF-TOKEN": csrf_token},
    )
    assert login_resp.status_code in {200, 201, 204}, login_resp.text
    return client.cookies.get("XSRF-TOKEN") or csrf_token


def test_accounts_package_exports_have_no_legacy_controllers_or_listeners() -> None:
    assert "listeners" not in accounts_pkg.__all__
    assert set(accounts_pkg.controllers.__all__) == {
        "ApiKeyController",
        "ProfileController",
        "RoleController",
        "UserController",
    }


async def test_unauthenticated_and_rbac_boundaries(tmp_path: Path) -> None:
    app, db_cfg, _ = await _build_accounts_app(tmp_path, "rbac.sqlite3")
    await _seed_user(db_cfg, email="member@example.com")
    await _seed_user(db_cfg, email="admin@example.com", is_superuser=True)

    async with AsyncTestClient(app=app) as client:
        for path in ("/api/me", "/api/me/api-keys", "/api/users", "/api/roles"):
            resp = await client.get(path)
            assert resp.status_code == 401

        await _login(client, "member@example.com")
        assert (await client.get("/api/me")).status_code == 200
        assert (await client.get("/api/users")).status_code == 403
        assert (await client.get("/api/roles")).status_code == 403

    async with AsyncTestClient(app=app) as admin_client:
        csrf = await _login(admin_client, "admin@example.com")
        users_resp = await admin_client.get("/api/users")
        assert users_resp.status_code == 200
        payload = users_resp.json()
        assert payload["total"] == 2
        assert len(payload["items"]) == 2

        role_resp = await admin_client.post(
            "/api/roles",
            json={"name": "Support"},
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert role_resp.status_code == 201
        role_slug = role_resp.json()["slug"]
        assert role_slug == "support"

        assign_resp = await admin_client.post(
            f"/api/roles/{role_slug}/assign",
            json={"userName": "member@example.com"},
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert assign_resp.status_code == 201

        revoke_resp = await admin_client.post(
            f"/api/roles/{role_slug}/revoke",
            json={"userName": "member@example.com"},
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert revoke_resp.status_code == 201


async def test_signed_in_accounts_need_application_access(tmp_path: Path) -> None:
    app, db_cfg, _ = await _build_accounts_app(tmp_path, "application_access.sqlite3")
    await _seed_user(db_cfg, email="no-access@example.com", application_access=False)
    await _seed_user(db_cfg, email="root@example.com", is_superuser=True, application_access=False)

    async with AsyncTestClient(app=app) as client:
        assert (await client.get("/api/csrf")).status_code == 200

        csrf = await _login(client, "no-access@example.com")
        denied = await client.get("/api/me")
        assert denied.status_code == 403
        assert denied.json()["code"] == APPLICATION_ACCESS_REQUIRED
        assert denied.json()["detail"] == "Your account does not have access to this application."

        signed_out = await client.post("/api/access/logout", headers={"X-XSRF-TOKEN": csrf})
        assert signed_out.status_code in {200, 201, 204}, signed_out.text
        assert (await client.get("/api/me")).status_code == 401

    async with AsyncTestClient(app=app) as superuser_client:
        await _login(superuser_client, "root@example.com")
        assert (await superuser_client.get("/api/me")).status_code == 200
        assert (await superuser_client.get("/api/users")).status_code == 200


async def test_profile_auth_modes_and_step_up(tmp_path: Path) -> None:
    app, db_cfg, clock_box = await _build_accounts_app(tmp_path, "profile_auth.sqlite3")
    alice = await _seed_user(db_cfg, email="alice@example.com", name="Alice")

    plugin = app.plugins.get(SecurityPlugin)
    assert plugin.config.api_key is not None
    store = plugin.config.api_key.store
    assert isinstance(store, SQLAlchemyAPIKeyStore)
    key_service = build_api_key_service(store, plugin.config.api_key.pepper, prefix=plugin.config.api_key.prefix)
    alice_key = await key_service.issue(
        subject_id=str(alice.id),
        restrictions=CredentialRestrictions(scopes=frozenset({"read", "mcp"})),
    )
    await store.update_metadata(alice_key.key_id, name="Alice Preseeded", key_prefix=alice_key.value[:12])

    async with AsyncTestClient(app=app) as key_client:
        headers = {"Authorization": f"Bearer {alice_key.value}"}
        me_resp = await key_client.get("/api/me", headers=headers)
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == "alice@example.com"

        assert (await key_client.patch("/api/me", json={"name": "Blocked"}, headers=headers)).status_code == 401
        assert (
            await key_client.patch(
                "/api/me/password",
                json={"currentPassword": "StrongPassword!123", "newPassword": "NewStrongPassword!456"},
                headers=headers,
            )
        ).status_code == 401
        assert (await key_client.delete("/api/me", headers=headers)).status_code == 401
        assert (await key_client.get("/api/me/api-keys", headers=headers)).status_code == 401

    clock_box[0] = datetime.now(UTC) - timedelta(minutes=10)
    async with AsyncTestClient(app=app) as stale_client:
        stale_csrf = await _login(stale_client, "alice@example.com")
        upd = await stale_client.patch("/api/me", json={"name": "Alice Updated"}, headers={"X-XSRF-TOKEN": stale_csrf})
        assert upd.status_code == 200
        assert upd.json()["name"] == "Alice Updated"

        pw_wrong = await stale_client.patch(
            "/api/me/password",
            json={"currentPassword": "WrongPassword!123", "newPassword": "NewStrongPassword!456"},
            headers={"X-XSRF-TOKEN": stale_csrf},
        )
        assert pw_wrong.status_code == 403
        pw_ok = await stale_client.patch(
            "/api/me/password",
            json={"currentPassword": "StrongPassword!123", "newPassword": "NewStrongPassword!456"},
            headers={"X-XSRF-TOKEN": stale_csrf},
        )
        assert pw_ok.status_code == 200

    async with AsyncTestClient(app=app) as del_client:
        del_csrf = await _login(del_client, "alice@example.com", password="NewStrongPassword!456")
        del_unconfirmed = await del_client.delete("/api/me", headers={"X-XSRF-TOKEN": del_csrf})
        assert del_unconfirmed.status_code == 403
        assert del_unconfirmed.json()["code"] == REAUTHENTICATION_REQUIRED
        del_ok = await del_client.request(
            "DELETE",
            "/api/me",
            json={"currentPassword": "NewStrongPassword!456"},
            headers={"X-XSRF-TOKEN": del_csrf},
        )
        assert del_ok.status_code == 204


async def test_admin_and_self_service_passwords_follow_the_password_policy(tmp_path: Path) -> None:
    app, alchemy_config, _ = await _build_accounts_app(tmp_path, "password_policy.sqlite3")
    await _seed_user(alchemy_config, email="root@example.com", is_superuser=True)

    async with AsyncTestClient(app=app) as client:
        headers = {"X-XSRF-TOKEN": await _login(client, "root@example.com")}

        too_short = await client.post(
            "/api/users",
            json={"email": "new.account@example.com", "password": "Short1!"},
            headers=headers,
        )
        assert too_short.status_code == 400
        assert too_short.json() == {
            "status": 400,
            "title": "Bad Request",
            "detail": "Password must be at least 12 characters long.",
        }

        created = await client.post(
            "/api/users",
            json={"email": "new.account@example.com", "password": "correct horse battery staple"},
            headers=headers,
        )
        assert created.status_code == 201, created.text

        same_as_email = await client.patch(
            f"/api/users/{created.json()['id']}",
            json={"password": "New.Account@Example.com"},
            headers=headers,
        )
        assert same_as_email.status_code == 400
        assert same_as_email.json()["detail"] == "Password must not be the same as the email address."

        too_common = await client.patch(
            "/api/me/password",
            json={"currentPassword": "StrongPassword!123", "newPassword": "Password12345"},
            headers=headers,
        )
        assert too_common.status_code == 400
        assert too_common.json()["detail"] == "Password is too common. Choose one that is harder to guess."

        changed = await client.patch(
            "/api/me/password",
            json={"currentPassword": "StrongPassword!123", "newPassword": "another long passphrase"},
            headers=headers,
        )
        assert changed.status_code == 200, changed.text


async def test_an_admin_password_change_signs_the_user_out_everywhere(tmp_path: Path) -> None:
    app, alchemy_config, _ = await _build_accounts_app(tmp_path, "admin_password_change.sqlite3")
    await _seed_user(alchemy_config, email="root@example.com", is_superuser=True)
    alice = await _seed_user(alchemy_config, email="alice@example.com")

    async with AsyncTestClient(app=app) as alice_client, AsyncTestClient(app=app) as admin_client:
        await _login(alice_client, "alice@example.com")
        assert (await alice_client.get("/api/me")).status_code == 200

        changed = await admin_client.patch(
            f"/api/users/{alice.id}",
            json={"password": "correct horse battery staple", "name": "Alice Renamed"},
            headers={"X-XSRF-TOKEN": await _login(admin_client, "root@example.com")},
        )
        assert changed.status_code == 200, changed.text
        assert changed.json()["name"] == "Alice Renamed"
        assert changed.json()["hasPassword"] is True

        assert (await alice_client.get("/api/me")).status_code == 401

    async with AsyncTestClient(app=app) as alice_client:
        await _login(alice_client, "alice@example.com", password="correct horse battery staple")
    async with alchemy_config.get_session() as db_session:
        stored = await db_session.get(m.User, alice.id)
        assert stored is not None
        assert stored.security_epoch == alice.security_epoch + 1


async def test_password_confirmation_attempts_are_rate_limited(tmp_path: Path) -> None:
    app, db_cfg, clock_box = await _build_accounts_app(tmp_path, "reauth_limit.sqlite3")
    await _seed_user(db_cfg, email="alice@example.com", name="Alice")

    clock_box[0] = datetime.now(UTC) - timedelta(minutes=10)
    async with AsyncTestClient(app=app) as client:
        headers = {"X-XSRF-TOKEN": await _login(client, "alice@example.com")}
        guess = {"name": "Guessed Key", "currentPassword": "WrongPassword!123"}
        statuses = [(await client.post("/api/me/api-keys", json=guess, headers=headers)).status_code for _ in range(11)]

    assert statuses == [403] * 10 + [429]


async def test_api_key_lifecycle_reconfirmation_and_cross_user_isolation(tmp_path: Path) -> None:
    app, db_cfg, clock_box = await _build_accounts_app(tmp_path, "api_keys.sqlite3")
    await _seed_user(db_cfg, email="alice@example.com", name="Alice")
    await _seed_user(db_cfg, email="bob@example.com", name="Bob")

    clock_box[0] = datetime.now(UTC) - timedelta(minutes=10)
    async with AsyncTestClient(app=app) as stale_client:
        stale_csrf = await _login(stale_client, "alice@example.com")
        stale_headers = {"X-XSRF-TOKEN": stale_csrf}
        unconfirmed = await stale_client.post(
            "/api/me/api-keys", json={"name": "Blocked Key", "scopes": ["read"]}, headers=stale_headers
        )
        assert unconfirmed.status_code == 403
        assert unconfirmed.json()["code"] == REAUTHENTICATION_REQUIRED

        wrong_password = await stale_client.post(
            "/api/me/api-keys",
            json={"name": "Blocked Key", "scopes": ["read"], "currentPassword": "WrongPassword!123"},
            headers=stale_headers,
        )
        assert wrong_password.status_code == 403
        assert "code" not in wrong_password.json()

        confirmed = await stale_client.post(
            "/api/me/api-keys",
            json={"name": "Confirmed Key", "scopes": ["read"], "currentPassword": "StrongPassword!123"},
            headers=stale_headers,
        )
        assert confirmed.status_code == 201
        confirmed_key_id = confirmed.json()["id"]

        rotate_path = f"/api/me/api-keys/{confirmed_key_id}/rotate"
        assert (await stale_client.post(rotate_path, headers=stale_headers)).status_code == 403
        rotated_confirmed = await stale_client.post(
            rotate_path, json={"currentPassword": "StrongPassword!123"}, headers=stale_headers
        )
        assert rotated_confirmed.status_code == 201

        revoke_path = f"/api/me/api-keys/{rotated_confirmed.json()['id']}"
        assert (await stale_client.delete(revoke_path, headers=stale_headers)).status_code == 403
        revoked_confirmed = await stale_client.request(
            "DELETE", revoke_path, json={"currentPassword": "StrongPassword!123"}, headers=stale_headers
        )
        assert revoked_confirmed.status_code == 204

    clock_box[0] = datetime.now(UTC)
    async with AsyncTestClient(app=app) as alice_client:
        csrf = await _login(alice_client, "alice@example.com")
        created_key = await alice_client.post(
            "/api/me/api-keys",
            json={"name": "MCP Key", "scopes": ["mcp"], "expiresInDays": 30},
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert created_key.status_code == 201
        created_data = created_key.json()
        assert created_data["secret"].startswith("lsk_")
        assert created_data["scopes"] == ["mcp"]
        created_key_id = created_data["id"]

        listed = await alice_client.get("/api/me/api-keys")
        assert listed.status_code == 200
        assert created_key_id in {item["id"] for item in listed.json()}
        assert all("secret" not in item for item in listed.json())

        rotated = await alice_client.post(
            f"/api/me/api-keys/{created_key_id}/rotate",
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert rotated.status_code == 201
        rotated_id = rotated.json()["id"]
        assert rotated_id != created_key_id

        revoked = await alice_client.delete(
            f"/api/me/api-keys/{created_key_id}",
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert revoked.status_code == 204

    async with AsyncTestClient(app=app) as bob_client:
        bob_csrf = await _login(bob_client, "bob@example.com")
        assert (
            await bob_client.delete(f"/api/me/api-keys/{rotated_id}", headers={"X-XSRF-TOKEN": bob_csrf})
        ).status_code == 404
        assert (
            await bob_client.post(f"/api/me/api-keys/{rotated_id}/rotate", headers={"X-XSRF-TOKEN": bob_csrf})
        ).status_code == 404


async def test_mfa_enrollment_enforces_login_challenge_and_expired_key_rotation_rejected(tmp_path: Path) -> None:
    import pyotp
    from sqlalchemy import select, update

    app, db_cfg, _ = await _build_accounts_app(tmp_path, "mfa_and_expired.sqlite3")
    alice = await _seed_user(db_cfg, email="mfa-alice@example.com", name="MFA Alice")

    async with AsyncTestClient(app=app) as client:
        csrf = await _login(client, "mfa-alice@example.com")

        expired_key = await client.post(
            "/api/me/api-keys",
            json={"name": "Soon Expired", "scopes": ["read"], "expiresInDays": 1},
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert expired_key.status_code == 201
        expired_id = expired_key.json()["id"]
        async with db_cfg.get_session() as session:
            await session.execute(
                update(m.APIKey)
                .where(m.APIKey.key_id == expired_id)
                .values(expires_at=datetime.now(UTC) - timedelta(hours=1))
            )
            await session.commit()
        assert (
            await client.post(f"/api/me/api-keys/{expired_id}/rotate", headers={"X-XSRF-TOKEN": csrf})
        ).status_code == 409

        step_up = await client.post(
            "/api/access/step-up/totp-enroll",
            json={"method": "password", "credential": "StrongPassword!123"},
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert step_up.status_code in {200, 201}, step_up.text
        step_up_grant = step_up.json()["grant"]

        enroll = await client.post(
            "/api/access/mfa/totp/enroll",
            json={"label": "mfa-alice@example.com", "step_up_grant": step_up_grant},
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert enroll.status_code in {200, 201}, enroll.text
        enroll_data = enroll.json()
        uri = enroll_data["provisioning_uri"]
        totp = pyotp.parse_uri(uri)
        assert isinstance(totp, pyotp.TOTP)
        confirm = await client.post(
            "/api/access/mfa/totp/verify",
            json={"enrollment_id": enroll_data["enrollment_id"], "code": totp.now()},
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert confirm.status_code in {200, 201}, confirm.text
        assert len(confirm.json()["codes"]) >= 1

    async with AsyncTestClient(app=app) as second_client:
        boot = await second_client.get("/api/csrf")
        assert boot.status_code == 200
        csrf2 = second_client.cookies.get("XSRF-TOKEN") or ""
        login_resp = await second_client.post(
            "/api/access/login",
            json={"identifier": "mfa-alice@example.com", "password": "StrongPassword!123"},
            headers={"X-XSRF-TOKEN": csrf2},
        )
        assert login_resp.status_code == 403, login_resp.text

    plugin = app.plugins.get(SecurityPlugin)
    assert plugin.config.local_auth is not None
    assert plugin.config.mfa is not None
    assert plugin.config.mfa.login_methods is not None
    methods = await plugin.config.mfa.login_methods.list_methods(str(alice.id))
    totp_method = next(item for item in methods if item.kind == "totp")
    from litestar_security.accounts import SecurityEvent

    outcome = await plugin.config.mfa.login_methods.revoke_login_method(
        str(alice.id),
        totp_method.method_id,
        require_remaining=False,
        event=SecurityEvent(
            event_id="evt-remove-totp",
            occurred_at=datetime.now(UTC),
            operation="mfa.totp.remove",
            outcome="success",
            account_id=str(alice.id),
            mechanism="mfa",
        ),
    )
    assert outcome.status.value == "revoked"
    async with db_cfg.get_session() as session:
        remaining = (await session.scalars(select(m.UserMFAFactor).where(m.UserMFAFactor.user_id == alice.id))).all()
        assert remaining == []
