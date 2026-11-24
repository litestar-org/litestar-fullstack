"""Unit tests for accounts services, AccountServices ServiceGroup, FilterSet, deps, and schemas."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import msgspec
import pytest
from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.filters import FilterGroup, LimitOffsetFilter, OrderByFilter, SearchFilter
from litestar.exceptions import PermissionDeniedException
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

        authed = await service.authenticate("alice@example.com", "StrongPassword!123")
        assert authed.id == created.id

        with pytest.raises(PermissionDeniedException):
            await service.update_password(
                {"current_password": "WrongPassword!999", "new_password": "NewStrongPassword!456"},
                db_obj=created,
            )

        initial_epoch = created.security_epoch
        await service.update_password(
            {"current_password": "StrongPassword!123", "new_password": "NewStrongPassword!456"},
            db_obj=created,
        )
        authed_after = await service.authenticate("alice@example.com", "NewStrongPassword!456")
        assert authed_after.security_epoch == initial_epoch + 1

        await service.update({"is_active": False}, item_id=created.id, auto_commit=True)
        with pytest.raises(PermissionDeniedException):
            await service.update_password(
                {"current_password": "NewStrongPassword!456", "new_password": "AnotherStrongPass!789"},
                db_obj=created,
            )


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
    user_filters = UserFilterSet(searchString="alice", page=2, pageSize=10, orderBy="email", sortOrder="asc").to_statement_filters()
    search_groups = [item for item in user_filters if isinstance(item, FilterGroup)]
    assert len(search_groups) == 1
    assert any(isinstance(sub, SearchFilter) for sub in search_groups[0].filters)
    assert any(isinstance(item, OrderByFilter) for item in user_filters)
    assert any(isinstance(item, LimitOffsetFilter) for item in user_filters)

    role_filters = RoleFilterSet(searchString="admin", page=1, pageSize=20, orderBy="name", sortOrder="asc").to_statement_filters()
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
