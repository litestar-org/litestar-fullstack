"""Unit/HTTP tests for TagService slug generation and TagController auth/guards."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from advanced_alchemy.base import orm_registry
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar import Litestar, get
from litestar.testing import AsyncTestClient
from litestar_security import CSRF_REQUIRED_OPT_KEY, SecurityPlugin, public
from litestar_security.accounts import Argon2PasswordHasher
from litestar_security.context import CredentialRestrictions

from app.db import models as m
from app.domain.accounts.security import (
    SQLAlchemyAPIKeyStore,
    build_api_key_service,
    build_csrf_config,
    build_security_config,
    build_session_middleware,
    build_session_store,
)
from app.domain.tags.controllers import TagController
from app.domain.tags.services import TagService
from app.lib.secrets import API_KEY_PEPPER_INFO, derive_subkey
from app.lib.settings import AppSettings, DatabaseSettings, SecuritySettings, Settings

if TYPE_CHECKING:
    from pathlib import Path

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

pytestmark = pytest.mark.anyio


async def _build_tags_app(tmp_path: Path, name: str) -> tuple[Litestar, SQLAlchemyAsyncConfig, Settings]:
    db_cfg = DatabaseSettings(URL=f"sqlite+aiosqlite:///{tmp_path / name}").get_config()
    async with db_cfg.get_engine().begin() as conn:
        await conn.run_sync(orm_registry.metadata.create_all)

    settings = Settings(
        app=AppSettings(SECRET_KEY="tags-test-secret", COOKIE_SECURE=False),
        security=SecuritySettings(COOKIE_SECURE=False),
    )

    @get("/api/csrf", opt={"auth": public(), CSRF_REQUIRED_OPT_KEY: True})
    async def csrf_bootstrap() -> dict[str, bool]:
        return {"ok": True}

    sec_cfg = build_security_config(settings, db_cfg)
    app = Litestar(
        route_handlers=[csrf_bootstrap, TagController],
        plugins=[SQLAlchemyPlugin(config=db_cfg), SecurityPlugin(sec_cfg)],
        middleware=[build_session_middleware(settings)],
        csrf_config=build_csrf_config(settings),
        stores={"sessions": build_session_store(db_cfg)},
    )
    return app, db_cfg, settings


async def _seed_user(db_cfg: SQLAlchemyAsyncConfig, *, email: str, is_superuser: bool = False) -> m.User:
    hashed = await Argon2PasswordHasher().hash("StrongPassword!123")
    async with db_cfg.get_session() as session:
        user = m.User(
            email=email,
            name="Tag User",
            hashed_password=hashed,
            is_active=True,
            is_verified=True,
            is_superuser=is_superuser,
        )
        session.add(user)
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


async def test_tag_service_slugs_and_controller_auth_matrix(tmp_path: Path) -> None:
    app, db_cfg, settings = await _build_tags_app(tmp_path, "tags.sqlite3")
    regular = await _seed_user(db_cfg, email="user@example.com", is_superuser=False)
    superuser = await _seed_user(db_cfg, email="admin@example.com", is_superuser=True)

    async with TagService.new(config=db_cfg) as tag_svc:
        t1 = await tag_svc.create({"name": "Python API"}, auto_commit=True)
        t2 = await tag_svc.create({"name": "Python API"}, auto_commit=True)
        assert t1.slug == "python-api"
        assert t2.slug != t1.slug

    key_svc = build_api_key_service(
        SQLAlchemyAPIKeyStore(db_cfg),
        derive_subkey(settings.app.SECRET_KEY, API_KEY_PEPPER_INFO),
    )
    issued = await key_svc.issue(
        subject_id=str(regular.id),
        restrictions=CredentialRestrictions(scopes=frozenset({"read", "write", "mcp"})),
    )

    async with AsyncTestClient(app=app) as api_client:
        await api_client.get("/api/csrf")
        api_csrf = api_client.cookies.get("XSRF-TOKEN") or ""
        headers = {"Authorization": f"Bearer {issued.value}", "X-XSRF-TOKEN": api_csrf}
        listed = await api_client.get("/api/tags", headers=headers)
        assert listed.status_code == 200
        assert listed.json()["total"] == 2

        created = await api_client.post("/api/tags", json={"name": "Litestar"}, headers=headers)
        assert created.status_code == 201, created.text
        created_id = created.json()["id"]

        assert (await api_client.get(f"/api/tags/{created_id}", headers=headers)).status_code == 401
        assert (
            await api_client.patch(f"/api/tags/{created_id}", json={"name": "Denied"}, headers=headers)
        ).status_code == 401

    async with AsyncTestClient(app=app) as user_client:
        csrf = await _login(user_client, regular.email)
        assert (await user_client.get(f"/api/tags/{created_id}")).status_code == 200
        assert (
            await user_client.patch(
                f"/api/tags/{created_id}",
                json={"name": "Nope"},
                headers={"X-XSRF-TOKEN": csrf},
            )
        ).status_code == 403
        assert (
            await user_client.delete(f"/api/tags/{created_id}", headers={"X-XSRF-TOKEN": csrf})
        ).status_code == 403

    async with AsyncTestClient(app=app) as admin_client:
        csrf = await _login(admin_client, superuser.email)
        updated = await admin_client.patch(
            f"/api/tags/{created_id}",
            json={"name": "Litestar Updated"},
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert updated.status_code == 200
        deleted = await admin_client.delete(f"/api/tags/{created_id}", headers={"X-XSRF-TOKEN": csrf})
        assert deleted.status_code in {200, 204}
