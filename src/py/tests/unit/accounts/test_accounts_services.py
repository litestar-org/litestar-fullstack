"""Unit tests for accounts services, AccountServices ServiceGroup, FilterSet, deps, and schemas."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

import msgspec
import pytest
from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.filters import FilterGroup, LimitOffsetFilter, OrderByFilter, SearchFilter
from litestar.exceptions import ClientException, PermissionDeniedException
from litestar_security.accounts import Argon2PasswordHasher
from sqlalchemy.orm import undefer_group

from app.db import models as m
from app.domain.accounts.deps import USER_LOAD_OPTIONS, RoleFilterSet, UserFilterSet
from app.domain.accounts.schemas import APIKeyCreate, APIKeyIssued, APIKeyItem, User
from app.domain.accounts.services import AccountServices, RoleService, UserService
from app.lib.settings import DatabaseSettings

if TYPE_CHECKING:
    from pathlib import Path

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

pytestmark = pytest.mark.anyio

_HASHER = Argon2PasswordHasher()


async def _init_db(tmp_path: Path, name: str) -> SQLAlchemyAsyncConfig:
    db_cfg = DatabaseSettings(URL=f"sqlite+aiosqlite:///{tmp_path / name}").get_config()
    engine = db_cfg.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(UUIDv7AuditBase.metadata.create_all)
    return db_cfg


async def test_user_service_argon2_create_and_update_password(tmp_path: Path) -> None:
    db_cfg = await _init_db(tmp_path, "users_service.sqlite3")
    async with db_cfg.get_session() as session:
        service = UserService(session=session)
        created = await service.create(
            {"email": "alice@example.com", "name": "Alice", "password": "StrongPassword!123"},
            auto_commit=True,
        )
        loaded = await service.get(created.id, load=[undefer_group("security_sensitive")])
        assert loaded.hashed_password is not None
        assert loaded.hashed_password.startswith("$argon2")
        assert loaded.has_password is True

        with pytest.raises(PermissionDeniedException):
            await service.update_password(
                created,
                current_password="WrongPassword!999",
                new_password="NewStrongPassword!456",
            )

        initial_epoch = created.security_epoch
        now = datetime.now(UTC)
        signed_in = m.UserSession(
            session_id="alice-session",
            binding_id="alice-binding",
            binding_digest="00" * 32,
            user_id=created.id,
            security_epoch=initial_epoch,
            authenticated_at=now,
            last_seen_at=now,
            expires_at=now + timedelta(hours=1),
        )
        session.add(signed_in)
        await session.commit()
        await service.update_password(
            created,
            current_password="StrongPassword!123",
            new_password="NewStrongPassword!456",
        )
        updated = await service.get(created.id, load=[undefer_group("security_sensitive")])
        assert (await _HASHER.verify(updated.hashed_password, "NewStrongPassword!456")).verified
        assert updated.security_epoch == initial_epoch + 1
        await session.refresh(signed_in)
        assert signed_in.revoked_at is not None

        await service.update({"is_active": False}, item_id=created.id, auto_commit=True)
        with pytest.raises(PermissionDeniedException):
            await service.update_password(
                created,
                current_password="NewStrongPassword!456",
                new_password="AnotherStrongPass!789",
            )


async def test_user_service_applies_the_password_policy_wherever_a_password_is_set(tmp_path: Path) -> None:
    alchemy_config = await _init_db(tmp_path, "users_password_policy.sqlite3")
    async with alchemy_config.get_session() as db_session:
        users = UserService(session=db_session)

        with pytest.raises(ClientException, match="at least 12 characters") as too_short:
            await users.create({"email": "alice@example.com", "password": "Short1!"})
        assert too_short.value.status_code == 400
        with pytest.raises(ClientException, match="same as the email address"):
            await users.create({"email": "Alice@Example.com", "password": "alice@example.com"})

        alice = await users.create(
            {"email": "alice@example.com", "password": "correct horse battery staple"},
            auto_commit=True,
        )
        with pytest.raises(ClientException, match="same as the email address"):
            await users.set_password(alice, "ALICE@example.com")
        with pytest.raises(ClientException, match="too common"):
            await users.set_password(alice, "Password12345")
        with pytest.raises(ClientException, match="must not exceed 128 characters"):
            await users.update_password(
                alice,
                current_password="correct horse battery staple",
                new_password="x" * 129,
            )


async def test_setting_a_password_advances_the_security_epoch_and_signs_the_user_out(tmp_path: Path) -> None:
    alchemy_config = await _init_db(tmp_path, "users_set_password.sqlite3")
    async with alchemy_config.get_session() as db_session:
        users = UserService(session=db_session)
        bob = await users.provision(email="bob@example.com", name="Bob", verified=True, now=datetime.now(UTC))
        now = datetime.now(UTC)
        signed_in = m.UserSession(
            session_id="bob-session",
            binding_id="bob-binding",
            binding_digest="00" * 32,
            user_id=bob.id,
            security_epoch=bob.security_epoch,
            authenticated_at=now,
            last_seen_at=now,
            expires_at=now + timedelta(hours=1),
        )
        db_session.add(signed_in)
        await db_session.commit()
        initial_epoch = bob.security_epoch

        await users.set_password(bob, "correct horse battery staple")
        await db_session.commit()

        await db_session.refresh(signed_in)
        assert signed_in.revoked_at is not None
        assert bob.security_epoch == initial_epoch + 1
        assert bob.has_password
        assert (await _HASHER.verify(bob.hashed_password, "correct horse battery staple")).verified


async def test_user_service_normalizes_emails_it_stores_and_looks_up(tmp_path: Path) -> None:
    alchemy_config = await _init_db(tmp_path, "users_email.sqlite3")
    async with alchemy_config.get_session() as db_session:
        users = UserService(session=db_session)

        created = await users.create({"email": " Alice@Example.COM ", "password": "StrongPassword!123"})
        assert created.email == "alice@example.com"

        provisioned = await users.provision(email="Bob@Example.com", name="Bob", verified=True, now=datetime.now(UTC))
        assert provisioned.email == "bob@example.com"

        renamed = await users.update({"email": "Carol@Example.com"}, item_id=provisioned.id)
        assert renamed.email == "carol@example.com"

        assert await users.find_by_email("ALICE@example.com ") is created
        assert await users.get_by_email(" CAROL@example.com") is renamed
        assert await users.find_by_email("nobody@example.com") is None


def test_account_ids_map_to_user_ids_and_back() -> None:
    user_id = UUID("01890a5d-ac96-774b-bcce-b302099a8057")

    assert UserService.to_user_id(str(user_id)) == user_id
    assert UserService.to_user_id("not-a-uuid") is None
    assert UserService.to_user_id("") is None
    assert UserService.to_user_id(None) is None


async def test_role_service_generates_unique_slugs(tmp_path: Path) -> None:
    db_cfg = await _init_db(tmp_path, "roles_service.sqlite3")
    async with db_cfg.get_session() as session:
        roles = RoleService(session=session)
        r1 = await roles.create({"name": "Billing Admin"}, auto_commit=True)
        r2 = await roles.create({"name": "Billing Admin "}, auto_commit=True)
        assert r1.slug == "billing-admin"
        assert r2.slug.startswith("billing-admin")
        assert r2.slug != r1.slug


async def test_account_services_group_atomic_transaction_and_rollback(tmp_path: Path) -> None:
    db_cfg = await _init_db(tmp_path, "account_group.sqlite3")
    async with AccountServices.new(config=db_cfg) as accounts:
        user = await accounts.users.create({"email": "group@example.com", "password": "StrongPassword!123"})
        role = await accounts.roles.create({"name": "Operator"})
        await accounts.user_roles.create({"user_id": user.id, "role_id": role.id, "assigned_at": datetime.now(UTC)})
        await accounts.audit_logs.log_action(action="role.assigned", actor_id=user.id, target_id=str(role.id))
        await accounts.session.commit()

    async with AccountServices.new(config=db_cfg) as accounts:
        found_user = await accounts.users.get_one_or_none(email="group@example.com")
        assert found_user is not None
        logs, total = await accounts.audit_logs.get_many_and_count()
        assert total == 1
        assert logs[0].action == "role.assigned"

    async with AccountServices.new(config=db_cfg) as accounts:
        await accounts.users.create({"email": "rolledback@example.com", "password": "StrongPassword!123"})
        await accounts.session.rollback()

    async with AccountServices.new(config=db_cfg) as accounts:
        assert await accounts.users.get_one_or_none(email="rolledback@example.com") is None


async def test_users_service_eager_loads_mfa_factors_and_serializes_schema(tmp_path: Path) -> None:
    db_cfg = await _init_db(tmp_path, "users_eager.sqlite3")
    async with db_cfg.get_session() as session:
        service = UserService(session=session)
        user = await service.create(
            {"email": "mfa-user@example.com", "name": "MFA User", "password": "StrongPassword!123"},
            auto_commit=True,
        )
        session.add(
            m.UserMFAFactor(
                method_id="totp-1",
                user_id=user.id,
                kind="totp",
                secret_ciphertext=b"ciphertext",
                key_version="v1",
                is_confirmed=True,
            )
        )
        await session.commit()

    async with db_cfg.get_session() as session:
        service = UserService(session=session, load=USER_LOAD_OPTIONS, uniquify=True)
        loaded = await service.get(user.id)
        schema = service.to_schema(loaded, schema_type=User)
        assert schema.is_two_factor_enabled is True
        assert schema.has_password is True
        assert schema.email == "mfa-user@example.com"


def test_filter_sets_and_api_key_schemas_camel_case() -> None:
    user_filters = UserFilterSet(
        searchString="alice", page=2, pageSize=10, orderBy="email", sortOrder="asc"
    ).to_statement_filters()
    search_groups = [item for item in user_filters if isinstance(item, FilterGroup)]
    assert len(search_groups) == 1
    assert any(isinstance(sub, SearchFilter) for sub in search_groups[0].filters)
    assert any(isinstance(item, OrderByFilter) for item in user_filters)
    assert any(isinstance(item, LimitOffsetFilter) for item in user_filters)

    role_filters = RoleFilterSet(
        searchString="admin", page=1, pageSize=20, orderBy="name", sortOrder="asc"
    ).to_statement_filters()
    role_groups = [item for item in role_filters if isinstance(item, FilterGroup)]
    assert len(role_groups) == 1
    assert any(isinstance(sub, SearchFilter) for sub in role_groups[0].filters)

    now = datetime.now(UTC)
    create_json = msgspec.json.encode(APIKeyCreate(name="CI Token", scopes=["mcp"], expires_in_days=30)).decode()
    assert '"expiresInDays":30' in create_json

    issued_json = msgspec.json.encode(
        APIKeyIssued(id="k1", name="CI Token", prefix="lsk_ab12", secret="lsk_full", scopes=["mcp"], created_at=now)
    ).decode()
    assert '"createdAt":' in issued_json
    assert '"expiresAt":null' in issued_json

    item_json = msgspec.json.encode(
        APIKeyItem(id="k1", name="CI Token", prefix="lsk_ab12", scopes=["mcp"], created_at=now)
    ).decode()
    assert '"lastUsedAt":null' in item_json
    assert '"revokedAt":null' in item_json
