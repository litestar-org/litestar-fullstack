"""Unit and conformance tests for SQLAlchemySecurityBackend, rate limiting, and audit event sink."""

from __future__ import annotations

import asyncio
from base64 import urlsafe_b64encode
from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, cast
from uuid import NAMESPACE_DNS, UUID, uuid5

import pytest
from advanced_alchemy.base import orm_registry
from advanced_alchemy.exceptions import RepositoryError
from litestar_security.accounts import (
    CreateSessionCommand,
    LoginMethod,
    PasswordChangeStatus,
    PasswordResetStatus,
    PurposeTokenCodec,
    PurposeTokenDelivery,
    RateLimitPolicy,
    RegistrationCommand,
    RegistrationStatus,
    RevokeLoginMethodStatus,
    SecurityEvent,
    TokenPurpose,
    VerificationStatus,
)
from litestar_security.authentication import InvalidCredentials, VerificationUnavailable
from litestar_security.testing import (
    StoreConformanceFactories,
    assert_rate_limiter_conformance,
    assert_security_backend_conformance,
    assert_session_registry_conformance,
)
from sqlalchemy import inspect as sa_inspect
from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError

from app.db import models as m
from app.domain.accounts.security import (
    AuditSecurityEventSink,
    SQLAlchemySecurityBackend,
    build_rate_limiter,
    sanitize_event_details,
)
from app.lib.constants import DEFAULT_ACCESS_ROLE
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


def _event(operation: str) -> SecurityEvent:
    return SecurityEvent(event_id=f"evt-{operation}", occurred_at=DEFAULT_NOW, operation=operation, outcome="success")


def _token_delivery(purpose: TokenPurpose, *, marker: int, maximum_attempts: int = 5) -> PurposeTokenDelivery:
    return PurposeTokenCodec(pepper=bytes(32), entropy=lambda length: bytes((marker,)) * length).issue(
        purpose,
        now=DEFAULT_NOW,
        lifetime=timedelta(minutes=5),
        template=purpose.value,
        destination=f"{purpose.value}@example.com",
        maximum_attempts=maximum_attempts,
    )


def _session_command(account_id: str, *, marker: int) -> CreateSessionCommand:
    seed = bytes((marker,))
    return CreateSessionCommand(
        session_id=urlsafe_b64encode(seed * 32).rstrip(b"=").decode("ascii"),
        binding_id="sb_" + urlsafe_b64encode(seed * 16).rstrip(b"=").decode("ascii"),
        binding_digest=seed * 32,
        account_id=account_id,
        security_epoch=1,
        created_at=DEFAULT_NOW,
        authenticated_at=DEFAULT_NOW,
        expires_at=DEFAULT_NOW + timedelta(hours=1),
    )


async def _register(
    backend: SQLAlchemySecurityBackend,
    email: str,
    *,
    verification: PurposeTokenDelivery | None = None,
) -> str:
    outcome = await backend.register(
        RegistrationCommand(normalized_identifier=email, display_name="Audited"),
        "original-hash",
        invitation_digest=None,
        verification=verification,
        now=DEFAULT_NOW,
        event=_event("register"),
    )
    assert outcome.status is RegistrationStatus.CREATED
    assert outcome.account is not None
    return outcome.account.account_id


async def _audit_actions(cfg: SQLAlchemyAsyncConfig) -> Counter[str]:
    async with cfg.get_session() as db_session:
        return Counter((await db_session.scalars(select(m.AuditLog.action))).all())


async def _assert_audited(cfg: SQLAlchemyAsyncConfig, expected: Counter[str], operation: str) -> None:
    expected[f"security.{operation}"] += 1
    assert await _audit_actions(cfg) == expected


async def test_local_account_and_session_conformance(tmp_path: Path) -> None:
    configs: list[SQLAlchemyAsyncConfig] = []
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


async def test_resolve_session_fails_closed_when_the_query_fails(tmp_path: Path) -> None:
    cfg = await _make_sqlite_config(tmp_path, "resolve_query_failure")
    try:
        async with cfg.get_engine().begin() as conn:
            await conn.execute(text("DROP TABLE auth_session"))
        backend = SQLAlchemySecurityBackend(cfg, clock=lambda: DEFAULT_NOW)

        resolved = await backend.resolve_session("missing-session", _uuid_identifier("resolve-user", 1))

        assert isinstance(resolved, VerificationUnavailable)
    finally:
        await cfg.get_engine().dispose()


async def test_a_failed_write_is_not_reported_as_a_duplicate(tmp_path: Path) -> None:
    cfg = await _make_sqlite_config(tmp_path, "failed_writes")
    try:
        account_id = _uuid_identifier("failed-write-user", 1)
        await _seed_user(cfg, account_id)
        async with cfg.get_engine().begin() as connection:
            for table_name in ("user_account", "auth_session"):
                await connection.execute(text(f'ALTER TABLE "{table_name}" RENAME TO "{table_name}_rows"'))
                await connection.execute(text(f'CREATE VIEW "{table_name}" AS SELECT * FROM "{table_name}_rows"'))
        backend = SQLAlchemySecurityBackend(cfg, clock=lambda: DEFAULT_NOW)

        failed_writes = {
            "registration": backend.register(
                RegistrationCommand(normalized_identifier="new-account@example.com"),
                "password-hash",
                invitation_digest=None,
                verification=None,
                now=DEFAULT_NOW,
                event=_event("register"),
            ),
            "session": backend.create(_session_command(account_id, marker=1), event=_event("session.create")),
        }
        reported: dict[str, object] = {}
        for write, failed_write in failed_writes.items():
            try:
                reported[write] = await failed_write
            except RepositoryError as error:
                reported[write] = type(error.__cause__)
            except ValueError as error:
                reported[write] = error
        assert reported == dict.fromkeys(failed_writes, OperationalError)
    finally:
        await cfg.get_engine().dispose()


async def test_register_returns_the_default_role_and_consumes_an_invitation_once(tmp_path: Path) -> None:
    cfg = await _make_sqlite_config(tmp_path, "register_invitation")
    try:
        async with cfg.get_session() as db_session:
            db_session.add(m.Role(name=DEFAULT_ACCESS_ROLE, slug="user"))
            await db_session.commit()
        backend = SQLAlchemySecurityBackend(cfg, clock=lambda: DEFAULT_NOW)
        invitation, notification = _token_delivery(TokenPurpose.INVITATION, marker=1).bind("pending-invitation")
        await backend.issue(invitation, notification, event=_event("invitation.issue"))

        invited = await backend.register(
            RegistrationCommand(normalized_identifier="invited@example.com", display_name="Invited"),
            "original-hash",
            invitation_digest=invitation.digest,
            verification=None,
            now=DEFAULT_NOW,
            event=_event("register"),
        )
        reused = await backend.register(
            RegistrationCommand(normalized_identifier="second@example.com", display_name="Second"),
            "original-hash",
            invitation_digest=invitation.digest,
            verification=None,
            now=DEFAULT_NOW,
            event=_event("register"),
        )

        assert invited.status is RegistrationStatus.CREATED
        assert invited.account is not None
        assert invited.account.verified is True
        assert invited.account.user is not None
        assert [assigned.role_name for assigned in invited.account.user.roles] == [DEFAULT_ACCESS_ROLE]
        assert reused.status is RegistrationStatus.INVALID_INVITATION
        assert await backend.find_for_login("second@example.com") is None
        assert (await _audit_actions(cfg))["security.register"] == 1
    finally:
        await cfg.get_engine().dispose()


async def test_successful_account_operations_commit_their_audit_event(tmp_path: Path) -> None:
    cfg = await _make_sqlite_config(tmp_path, "audit_accounts")
    try:
        backend = SQLAlchemySecurityBackend(cfg, clock=lambda: DEFAULT_NOW)
        expected: Counter[str] = Counter()

        verification = _token_delivery(TokenPurpose.VERIFICATION, marker=1)
        account_id = await _register(backend, "audited@example.com", verification=verification)
        await _assert_audited(cfg, expected, "register")

        verified = await backend.consume_and_verify(
            verification.issue.token_id, verification.issue.digest, now=DEFAULT_NOW, event=_event("verify")
        )
        assert verified.status is VerificationStatus.CONSUMED
        await _assert_audited(cfg, expected, "verify")

        assert await backend.compare_and_replace_password(
            account_id, "original-hash", "rehashed", event=_event("password.rehash")
        )
        await _assert_audited(cfg, expected, "password.rehash")

        changed = await backend.replace_password_and_bump_epoch(
            account_id, "changed-hash", expected_epoch=1, event=_event("password.change")
        )
        assert changed.status is PasswordChangeStatus.CHANGED
        await _assert_audited(cfg, expected, "password.change")

        recovery, notification = _token_delivery(TokenPurpose.RECOVERY, marker=2).bind(account_id, security_epoch=2)
        await backend.issue(recovery, notification, event=_event("recovery.issue"))
        await _assert_audited(cfg, expected, "recovery.issue")

        reset = await backend.consume_and_reset(
            recovery.token_id, recovery.digest, "reset-hash", now=DEFAULT_NOW, event=_event("password.reset")
        )
        assert (reset.status, reset.security_epoch) == (PasswordResetStatus.RESET, 3)
        password_state = await backend.get_password_state(account_id)
        assert password_state is not None
        assert (password_state.password_hash, password_state.security_epoch) == ("reset-hash", 3)
        await _assert_audited(cfg, expected, "password.reset")

        await backend.register_login_method(
            account_id, LoginMethod("totp-1", "totp", DEFAULT_NOW), event=_event("login_method.register")
        )
        await _assert_audited(cfg, expected, "login_method.register")

        revoked_method = await backend.revoke_login_method(account_id, "totp-1", event=_event("login_method.revoke"))
        assert revoked_method.status is RevokeLoginMethodStatus.REVOKED
        assert [method.method_id for method in await backend.list_methods(account_id)] == ["password"]
        await _assert_audited(cfg, expected, "login_method.revoke")
    finally:
        await cfg.get_engine().dispose()


async def test_successful_session_operations_commit_their_audit_event(tmp_path: Path) -> None:
    cfg = await _make_sqlite_config(tmp_path, "audit_sessions")
    try:
        backend = SQLAlchemySecurityBackend(cfg, clock=lambda: DEFAULT_NOW)
        account_id = await _register(backend, "sessions@example.com")
        expected = await _audit_actions(cfg)

        first, second, third = (_session_command(account_id, marker=marker) for marker in (1, 2, 3))
        await backend.create(first, event=_event("session.create"))
        await _assert_audited(cfg, expected, "session.create")

        assert await backend.rebind(first.session_id, second, event=_event("session.rebind")) is not None
        await _assert_audited(cfg, expected, "session.rebind")

        await backend.create(third, event=_event("session.create"))
        await _assert_audited(cfg, expected, "session.create")

        assert await backend.revoke_other_sessions(account_id, second.session_id, event=_event("session.revoke_others"))
        await _assert_audited(cfg, expected, "session.revoke_others")

        assert await backend.revoke_session_for_account(account_id, second.session_id, event=_event("session.revoke"))
        await _assert_audited(cfg, expected, "session.revoke")

        await backend.create(_session_command(account_id, marker=4), event=_event("session.create"))
        await _assert_audited(cfg, expected, "session.create")
        assert await backend.revoke_sessions_for_account(account_id, event=_event("session.revoke_all")) == 1
        await _assert_audited(cfg, expected, "session.revoke_all")
    finally:
        await cfg.get_engine().dispose()


async def test_rejected_operations_leave_no_audit_event(tmp_path: Path) -> None:
    cfg = await _make_sqlite_config(tmp_path, "audit_rejected")
    try:
        backend = SQLAlchemySecurityBackend(cfg, clock=lambda: DEFAULT_NOW)
        verification = _token_delivery(TokenPurpose.VERIFICATION, marker=1)
        account_id = await _register(backend, "rejected@example.com", verification=verification)
        recovery, notification = _token_delivery(TokenPurpose.RECOVERY, marker=2).bind(account_id, security_epoch=1)
        await backend.issue(recovery, notification, event=_event("recovery.issue"))
        committed = await _audit_actions(cfg)
        unknown_account_id = _uuid_identifier("unknown-account", 1)

        duplicate = await backend.register(
            RegistrationCommand(normalized_identifier="rejected@example.com", display_name="Again"),
            "other-hash",
            invitation_digest=None,
            verification=None,
            now=DEFAULT_NOW,
            event=_event("register"),
        )
        assert duplicate.status is RegistrationStatus.DUPLICATE

        wrong_proof = await backend.consume_and_verify(
            verification.issue.token_id, b"x" * 32, now=DEFAULT_NOW, event=_event("verify")
        )
        assert wrong_proof.status is VerificationStatus.INVALID

        assert not await backend.compare_and_replace_password(
            account_id, "stale-hash", "rehashed", event=_event("password.rehash")
        )

        stale_epoch = await backend.replace_password_and_bump_epoch(
            account_id, "changed-hash", expected_epoch=7, event=_event("password.change")
        )
        assert stale_epoch.status is PasswordChangeStatus.CONFLICT
        unknown_account = await backend.replace_password_and_bump_epoch(
            unknown_account_id, "changed-hash", expected_epoch=1, event=_event("password.change")
        )
        assert unknown_account.status is PasswordChangeStatus.NOT_FOUND

        async with cfg.get_session() as db_session:
            user = await db_session.get_one(m.User, UUID(account_id))
            user.security_epoch = 2
            await db_session.commit()
        outdated_recovery = await backend.consume_and_reset(
            recovery.token_id, recovery.digest, "reset-hash", now=DEFAULT_NOW, event=_event("password.reset")
        )
        assert outdated_recovery.status is PasswordResetStatus.CONFLICT

        missing_method = await backend.revoke_login_method(account_id, "totp-1", event=_event("login_method.revoke"))
        assert missing_method.status is RevokeLoginMethodStatus.NOT_FOUND
        await backend.register_login_method(
            account_id, LoginMethod("only-password", "password", DEFAULT_NOW), event=_event("login_method.register")
        )
        committed["security.login_method.register"] += 1
        final_method = await backend.revoke_login_method(
            account_id, "only-password", event=_event("login_method.revoke")
        )
        assert final_method.status is RevokeLoginMethodStatus.FINAL_METHOD
        assert [method.method_id for method in await backend.list_methods(account_id)] == ["only-password"]

        absent_session = _session_command(account_id, marker=1)
        assert not await backend.revoke_session_for_account(
            account_id, absent_session.session_id, event=_event("session.revoke")
        )
        assert await backend.revoke_sessions_for_account(account_id, event=_event("session.revoke_all")) == 0
        assert await backend.rebind("absent-session", absent_session, event=_event("session.rebind")) is None

        password_state = await backend.get_password_state(account_id)
        assert password_state is not None
        assert password_state.password_hash == "original-hash"
        assert await _audit_actions(cfg) == committed
    finally:
        await cfg.get_engine().dispose()


async def test_concurrent_failed_proofs_are_all_counted(tmp_path: Path) -> None:
    cfg = await _make_sqlite_config(tmp_path, "attempt_counter")
    try:
        backend = SQLAlchemySecurityBackend(cfg, clock=lambda: DEFAULT_NOW)
        counted = _token_delivery(TokenPurpose.VERIFICATION, marker=1, maximum_attempts=50)
        burned = _token_delivery(TokenPurpose.VERIFICATION, marker=2, maximum_attempts=3)
        await _register(backend, "counted@example.com", verification=counted)
        await _register(backend, "burned@example.com", verification=burned)

        async def present_wrong_proof(delivery: PurposeTokenDelivery) -> VerificationStatus:
            outcome = await backend.consume_and_verify(
                delivery.issue.token_id, b"x" * 32, now=DEFAULT_NOW, event=_event("verify")
            )
            return outcome.status

        counted_statuses = await asyncio.gather(*(present_wrong_proof(counted) for _ in range(12)))
        burned_statuses = await asyncio.gather(*(present_wrong_proof(burned) for _ in range(12)))
        after_burn = await backend.consume_and_verify(
            burned.issue.token_id, burned.issue.digest, now=DEFAULT_NOW, event=_event("verify")
        )

        async with cfg.get_session() as db_session:
            purpose_tokens = {
                purpose_token.token_id: purpose_token
                for purpose_token in (await db_session.scalars(select(m.PurposeToken))).all()
            }
        counted_token = purpose_tokens[counted.issue.token_id]
        burned_token = purpose_tokens[burned.issue.token_id]
        assert set(counted_statuses) == {VerificationStatus.INVALID}
        assert (counted_token.attempts, counted_token.consumed_at) == (12, None)
        rejected_before_burn = burned_statuses.count(VerificationStatus.INVALID)
        assert rejected_before_burn >= 3
        assert burned_token.attempts == rejected_before_burn
        assert burned_token.consumed_at is not None
        assert after_burn.status is VerificationStatus.USED
        assert "security.verify" not in await _audit_actions(cfg)
    finally:
        await cfg.get_engine().dispose()


async def test_touch_persists_last_seen_and_ignores_revoked_sessions(tmp_path: Path) -> None:
    cfg = await _make_sqlite_config(tmp_path, "touch_session")
    try:
        backend = SQLAlchemySecurityBackend(cfg, clock=lambda: DEFAULT_NOW)
        account_id = await _register(backend, "touch@example.com")
        command = _session_command(account_id, marker=1)
        await backend.create(command, event=_event("session.create"))
        seen_at = DEFAULT_NOW + timedelta(minutes=5)

        touched = await backend.touch(command.session_id, now=seen_at)
        stored = await backend.get(command.session_id)

        assert touched is not None
        assert touched.last_seen_at == seen_at
        assert stored == touched
        assert await backend.touch(command.session_id, now=DEFAULT_NOW + timedelta(hours=1)) is None
        await backend.revoke_session_for_account(account_id, command.session_id, event=_event("session.revoke"))
        assert await backend.touch(command.session_id, now=seen_at) is None
    finally:
        await cfg.get_engine().dispose()
