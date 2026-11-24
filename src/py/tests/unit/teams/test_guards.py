"""Unit/HTTP authorization tests for Teams SecureControllers and least-privilege MCP auth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from advanced_alchemy.base import orm_registry
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar import Litestar, get
from litestar.testing import AsyncTestClient
from litestar_queues import QueueConfig, QueuePlugin, WorkerConfig
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
from app.domain.teams.controllers import TeamController, TeamInvitationController, TeamMemberController
from app.lib.secrets import API_KEY_PEPPER_INFO, derive_subkey
from app.lib.settings import AppSettings, DatabaseSettings, SecuritySettings, Settings

if TYPE_CHECKING:
    from pathlib import Path

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

pytestmark = pytest.mark.anyio


async def _build_teams_app(tmp_path: Path, name: str) -> tuple[Litestar, SQLAlchemyAsyncConfig, Settings]:
    db_cfg = DatabaseSettings(URL=f"sqlite+aiosqlite:///{tmp_path / name}").get_config()
    async with db_cfg.get_engine().begin() as conn:
        await conn.run_sync(orm_registry.metadata.create_all)

    settings = Settings(
        app=AppSettings(SECRET_KEY="teams-guards-secret", COOKIE_SECURE=False),
        security=SecuritySettings(COOKIE_SECURE=False),
    )

    @get("/api/csrf", opt={"auth": public(), CSRF_REQUIRED_OPT_KEY: True})
    async def csrf_bootstrap() -> dict[str, bool]:
        return {"ok": True}

    sec_cfg = build_security_config(settings, db_cfg)
    queue_cfg = QueueConfig(
        queue_backend="memory",
        execution_backend="immediate",
        worker=WorkerConfig(placement="external"),
    )
    app = Litestar(
        route_handlers=[csrf_bootstrap, TeamController, TeamMemberController, TeamInvitationController],
        plugins=[
            SQLAlchemyPlugin(config=db_cfg),
            QueuePlugin(config=queue_cfg),
            SecurityPlugin(sec_cfg),
        ],
        middleware=[build_session_middleware(settings)],
        csrf_config=build_csrf_config(settings),
        stores={"sessions": build_session_store(db_cfg)},
    )
    return app, db_cfg, settings


async def _seed_user(
    db_cfg: SQLAlchemyAsyncConfig,
    *,
    email: str,
    name: str = "User",
    is_superuser: bool = False,
) -> m.User:
    hashed = await Argon2PasswordHasher().hash("StrongPassword!123")
    async with db_cfg.get_session() as session:
        user = m.User(
            email=email,
            name=name,
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
    csrf_token = client.cookies.get("XSRF-TOKEN") or ""
    resp = await client.post(
        "/api/access/login",
        json={"identifier": email, "password": "StrongPassword!123"},
        headers={"X-XSRF-TOKEN": csrf_token},
    )
    assert resp.status_code in {200, 201, 204}, resp.text
    return client.cookies.get("XSRF-TOKEN") or csrf_token


async def _seed_team_roles(
    db_cfg: SQLAlchemyAsyncConfig,
) -> tuple[str, m.User, m.User, m.User, m.User, m.User]:
    owner = await _seed_user(db_cfg, email="owner@example.com", name="Owner")
    admin = await _seed_user(db_cfg, email="admin@example.com", name="Admin")
    member = await _seed_user(db_cfg, email="member@example.com", name="Member")
    outsider = await _seed_user(db_cfg, email="outsider@example.com", name="Outsider")
    invitee = await _seed_user(db_cfg, email="invitee@example.com", name="Invitee")

    async with db_cfg.get_session() as session:
        team = m.Team(name="Alpha", slug="alpha")
        session.add(team)
        await session.flush()
        session.add_all(
            [
                m.TeamMember(team_id=team.id, user_id=owner.id, role=m.TeamRoles.ADMIN, is_owner=True),
                m.TeamMember(team_id=team.id, user_id=admin.id, role=m.TeamRoles.ADMIN, is_owner=False),
                m.TeamMember(team_id=team.id, user_id=member.id, role=m.TeamRoles.MEMBER, is_owner=False),
            ]
        )
        await session.commit()
        return str(team.id), owner, admin, member, outsider, invitee


async def test_team_role_guards_and_least_privilege_api_key_matrix(tmp_path: Path) -> None:
    app, db_cfg, settings = await _build_teams_app(tmp_path, "team_guards.sqlite3")
    team_id, owner, admin, member, outsider, invitee = await _seed_team_roles(db_cfg)

    key_svc = build_api_key_service(
        SQLAlchemyAPIKeyStore(db_cfg),
        derive_subkey(settings.app.SECRET_KEY, API_KEY_PEPPER_INFO),
    )
    issued = await key_svc.issue(
        subject_id=str(owner.id),
        restrictions=CredentialRestrictions(scopes=frozenset({"read", "write", "mcp"})),
    )

    async with AsyncTestClient(app=app) as api_client:
        headers = {"Authorization": f"Bearer {issued.value}"}
        assert (await api_client.get("/api/teams", headers=headers)).status_code == 200
        assert (await api_client.get(f"/api/teams/{team_id}", headers=headers)).status_code == 200
        assert (await api_client.post("/api/teams", json={"name": "Nope"}, headers=headers)).status_code == 401
        assert (
            await api_client.patch(f"/api/teams/{team_id}", json={"name": "Renamed"}, headers=headers)
        ).status_code == 401
        assert (await api_client.delete(f"/api/teams/{team_id}", headers=headers)).status_code == 401

    async with AsyncTestClient(app=app) as outsider_client:
        csrf = await _login(outsider_client, outsider.email)
        assert (await outsider_client.get(f"/api/teams/{team_id}")).status_code == 403
        assert (await outsider_client.get(f"/api/teams/{team_id}/invitations")).status_code == 403
        assert (
            await outsider_client.post(
                f"/api/teams/{team_id}/members",
                json={"userName": outsider.email},
                headers={"X-XSRF-TOKEN": csrf},
            )
        ).status_code == 403

    async with AsyncTestClient(app=app) as member_client:
        csrf = await _login(member_client, member.email)
        assert (await member_client.get(f"/api/teams/{team_id}")).status_code == 200
        assert (await member_client.get(f"/api/teams/{team_id}/invitations")).status_code == 200
        assert (
            await member_client.patch(
                f"/api/teams/{team_id}",
                json={"name": "MemberEdit"},
                headers={"X-XSRF-TOKEN": csrf},
            )
        ).status_code == 403
        assert (
            await member_client.post(
                f"/api/teams/{team_id}/invitations",
                json={"email": invitee.email, "role": "MEMBER"},
                headers={"X-XSRF-TOKEN": csrf},
            )
        ).status_code == 403

    async with AsyncTestClient(app=app) as admin_client:
        csrf = await _login(admin_client, admin.email)
        assert (
            await admin_client.patch(
                f"/api/teams/{team_id}",
                json={"description": "Updated by admin"},
                headers={"X-XSRF-TOKEN": csrf},
            )
        ).status_code == 200
        assert (await admin_client.delete(f"/api/teams/{team_id}", headers={"X-XSRF-TOKEN": csrf})).status_code == 403
        remove_owner = await admin_client.request(
            "DELETE",
            f"/api/teams/{team_id}/members",
            json={"userName": owner.email},
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert remove_owner.status_code == 400
        inv_resp = await admin_client.post(
            f"/api/teams/{team_id}/invitations",
            json={"email": invitee.email, "role": "MEMBER"},
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert inv_resp.status_code == 201, inv_resp.text
        invitation_id = inv_resp.json()["id"]

    async with AsyncTestClient(app=app) as outsider_accept_client:
        csrf = await _login(outsider_accept_client, outsider.email)
        wrong_user = await outsider_accept_client.post(
            f"/api/teams/{team_id}/invitations/{invitation_id}/accept",
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert wrong_user.status_code == 403

    async with AsyncTestClient(app=app) as invitee_client:
        csrf = await _login(invitee_client, invitee.email)
        accepted = await invitee_client.post(
            f"/api/teams/{team_id}/invitations/{invitation_id}/accept",
            headers={"X-XSRF-TOKEN": csrf},
        )
        assert accepted.status_code in {200, 201}, accepted.text

    async with AsyncTestClient(app=app) as owner_client:
        csrf = await _login(owner_client, owner.email)
        deleted = await owner_client.delete(f"/api/teams/{team_id}", headers={"X-XSRF-TOKEN": csrf})
        assert deleted.status_code in {200, 204}
