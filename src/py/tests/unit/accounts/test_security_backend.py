"""Unit and conformance tests for SQLAlchemySecurityBackend, rate limiting, and audit event sink."""

from __future__ import annotations

from base64 import urlsafe_b64encode
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, cast
from uuid import NAMESPACE_DNS, UUID, uuid5

import pytest
from advanced_alchemy.base import orm_registry
from litestar_security.accounts import CreateSessionCommand, RateLimitPolicy, SecurityEvent
from litestar_security.authentication import InvalidCredentials, VerificationUnavailable
from litestar_security.testing import (
    StoreConformanceFactories,
    assert_rate_limiter_conformance,
    assert_security_backend_conformance,
    assert_session_registry_conformance,
)
from sqlalchemy import inspect as sa_inspect
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from app.db import models as m
from app.domain.accounts.security import (
    AuditSecurityEventSink,
    SQLAlchemySecurityBackend,
    build_rate_limiter,
    sanitize_event_details,
)
from app.lib.settings import DatabaseSettings

if TYPE_CHECKING:
    from pathlib import Path

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

pytestmark = pytest.mark.anyio

DEFAULT_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _uuid_identifier(namespace: str, sequence: int) -> str:
    return str(uuid5(NAMESPACE_DNS, f"{namespace}:{sequence}"))


async def _make_sqlite_config(tmp_path: Path, name: str) -> SQLAlchemyAsyncConfig:
    db_file = tmp_path / f"{name}.sqlite3"
    cfg = DatabaseSettings(URL=f"sqlite+aiosqlite:///{db_file}").get_config()
    async with cfg.get_engine().begin() as conn:
        await conn.run_sync(orm_registry.metadata.create_all)
    return cfg


async def _seed_user(cfg: SQLAlchemyAsyncConfig, account_id: str) -> None:
    uid = UUID(account_id)
    async with cfg.get_session() as session:
        existing = await session.scalar(select(m.User.id).where(m.User.id == uid))
        if existing is None:
            session.add(m.User(id=uid, email=f"{account_id}@example.com", is_active=True, is_verified=True))
            await session.commit()


async def test_local_account_and_session_conformance(tmp_path: Path) -> None:
    counter = 0
    configs: list[SQLAlchemyAsyncConfig] = []

    def make_backend() -> SQLAlchemySecurityBackend:
        nonlocal counter
        counter += 1
        db_file = tmp_path / f"backend_{counter}.sqlite3"
        cfg = DatabaseSettings(URL=f"sqlite+aiosqlite:///{db_file}").get_config()
        configs.append(cfg)
        return SQLAlchemySecurityBackend(cfg, clock=lambda: DEFAULT_NOW)

    async def init_all_tables(cfg: SQLAlchemyAsyncConfig) -> None:
        async with cfg.get_engine().begin() as conn:
            await conn.run_sync(orm_registry.metadata.create_all)

    ready_backends: list[SQLAlchemySecurityBackend] = []
    for index in range(1, 5):
        cfg = await _make_sqlite_config(tmp_path, f"conf_backend_{index}")
        configs.append(cfg)
        for ns in (
            "conformance-account",
            "conformance-principal",
            "conformance-session-other",
            "conformance-session-owner",
            "conformance-subject",
        ):
            await _seed_user(cfg, _uuid_identifier(ns, 0))
        ready_backends.append(SQLAlchemySecurityBackend(cfg, clock=lambda: DEFAULT_NOW))

    iterator = iter(ready_backends)

    def factory() -> SQLAlchemySecurityBackend:
        return next(iterator)

    try:
        await assert_security_backend_conformance(
            StoreConformanceFactories(
                local_account_store=cast("Any", factory),
                session_registry=factory,
            ),
            identifiers=_uuid_identifier,
        )
    finally:
        for cfg in configs:
            await cfg.get_engine().dispose()


async def test_session_registry_conformance_standalone(tmp_path: Path) -> None:
    configs: list[SQLAlchemyAsyncConfig] = []
    ready: list[SQLAlchemySecurityBackend] = []
    for index in range(1, 3):
        cfg = await _make_sqlite_config(tmp_path, f"sess_reg_{index}")
        configs.append(cfg)
        for ns in ("conformance-session-owner", "conformance-session-other"):
            await _seed_user(cfg, _uuid_identifier(ns, 0))
        ready.append(SQLAlchemySecurityBackend(cfg, clock=lambda: DEFAULT_NOW))

    iterator = iter(ready)
    try:
        await assert_session_registry_conformance(
            lambda: next(iterator),
            now=DEFAULT_NOW,
            identifiers=_uuid_identifier,
        )
    finally:
        for cfg in configs:
            await cfg.get_engine().dispose()


async def test_rate_limiter_conformance(tmp_path: Path) -> None:
    cfg = await _make_sqlite_config(tmp_path, "rate_limit")
    try:
        await assert_rate_limiter_conformance(
            lambda limit: build_rate_limiter(
                cfg,
                policies={"conformance.rate_limit": RateLimitPolicy(limit=limit, window=timedelta(seconds=60))},
                clock=lambda: DEFAULT_NOW,
            ),
            limit=5,
            concurrency=20,
        )
    finally:
        await cfg.get_engine().dispose()


async def test_resolve_session_fail_closed_and_eager_loads(tmp_path: Path) -> None:
    cfg = await _make_sqlite_config(tmp_path, "resolve_session")
    try:
        async with cfg.get_session() as session:
            role = m.Role(name="Admin", slug="admin")
            team = m.Team(name="Core", slug="core")
            user = m.User(email="eager@example.com", name="Eager", is_active=True, is_verified=True)
            session.add_all([role, team, user])
            await session.flush()
            session.add(m.UserRole(user_id=user.id, role_id=role.id, assigned_at=DEFAULT_NOW))
            session.add(m.TeamMember(user_id=user.id, team_id=team.id, role=m.TeamRoles.ADMIN, is_owner=True))
            await session.commit()
            user_id = str(user.id)

        session_id = urlsafe_b64encode(b"s" * 32).rstrip(b"=").decode("ascii")
        binding_id = "sb_" + urlsafe_b64encode(b"b" * 16).rstrip(b"=").decode("ascii")
        backend = SQLAlchemySecurityBackend(cfg, clock=lambda: DEFAULT_NOW)
        created = await backend.create(
            CreateSessionCommand(
                session_id=session_id,
                binding_id=binding_id,
                binding_digest=b"b" * 32,
                account_id=user_id,
                security_epoch=1,
                created_at=DEFAULT_NOW,
                authenticated_at=DEFAULT_NOW,
                expires_at=DEFAULT_NOW + timedelta(hours=1),
                display_metadata={"device": "test"},
            ),
            event=SecurityEvent(
                event_id="evt-1",
                occurred_at=DEFAULT_NOW,
                operation="session.create",
                outcome="success",
            ),
        )
        assert created.session_id == session_id

        resolved = await backend.resolve_session(session_id, user_id, now=DEFAULT_NOW)
        assert not isinstance(resolved, InvalidCredentials | VerificationUnavailable)
        loaded_user = resolved.account.user
        assert loaded_user is not None
        unloaded = sa_inspect(loaded_user).unloaded
        assert "roles" not in unloaded
        assert "teams" not in unloaded
        assert "mfa_factors" not in unloaded
        assert len(loaded_user.roles) == 1
        assert len(loaded_user.teams) == 1

        revoked = await backend.revoke_session_for_account(
            user_id,
            session_id,
            event=SecurityEvent(
                event_id="evt-2",
                occurred_at=DEFAULT_NOW,
                operation="session.revoke",
                outcome="success",
            ),
        )
        assert revoked is True
        after_revoke = await backend.resolve_session(session_id, user_id, now=DEFAULT_NOW)
        assert isinstance(after_revoke, InvalidCredentials)

        class _BrokenConfig:
            def get_session(self) -> object:
                stmt = "SELECT 1"
                cause = RuntimeError()
                raise OperationalError(stmt, {}, cause)

        broken_backend = SQLAlchemySecurityBackend(_BrokenConfig(), clock=lambda: DEFAULT_NOW)  # type: ignore[arg-type]
        outage_result = await broken_backend.resolve_session(session_id, user_id, now=DEFAULT_NOW)
        assert isinstance(outage_result, VerificationUnavailable)
    finally:
        await cfg.get_engine().dispose()


async def test_audit_security_event_sink_persists_and_redacts(tmp_path: Path) -> None:
    cfg = await _make_sqlite_config(tmp_path, "audit_sink")
    try:
        user_id = _uuid_identifier("audit-user", 1)
        await _seed_user(cfg, user_id)
        sink = AuditSecurityEventSink(cfg, strict=True)

        await sink.emit(
            SecurityEvent(
                event_id="evt-auth-1",
                occurred_at=DEFAULT_NOW,
                operation="login",
                outcome="success",
                account_id=user_id,
                principal_id=user_id,
                mechanism="session",
                correlation={
                    "ip_address": "127.0.0.1",
                    "user_agent": "pytest-client",
                    "password": "plaintext-password",
                    "safe": "ok",
                },
            )
        )
        nested_sanitized = sanitize_event_details({"nested": {"recovery_code": "1234-5678", "safe": "ok"}})
        assert nested_sanitized["nested"]["recovery_code"] == "[REDACTED]"
        assert nested_sanitized["nested"]["safe"] == "ok"
        await sink.emit(
            SecurityEvent(
                event_id="evt-anon-1",
                occurred_at=DEFAULT_NOW,
                operation="login",
                outcome="failed",
                principal_id="not-a-uuid",
                correlation={"challenge": "raw-challenge"},
            )
        )

        async with cfg.get_session() as session:
            logs = (await session.scalars(select(m.AuditLog).order_by(m.AuditLog.created_at))).all()

        assert len(logs) == 2
        auth_log, anon_log = logs[0], logs[1]
        assert auth_log.actor_id == UUID(user_id)
        assert auth_log.action == "security.login"
        assert auth_log.ip_address == "127.0.0.1"
        assert auth_log.details is not None
        assert auth_log.details["correlation"]["password"] == "[REDACTED]"
        assert auth_log.details["correlation"]["safe"] == "ok"

        assert anon_log.actor_id is None
        assert anon_log.details is not None
        assert anon_log.details["raw_actor_id"] == "not-a-uuid"
        assert anon_log.details["correlation"]["challenge"] == "[REDACTED]"
    finally:
        await cfg.get_engine().dispose()
