"""SQLAlchemy persistence models for ``litestar-security`` stores and shared KV storage."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.extensions.litestar.store import StoreModelMixin
from advanced_alchemy.types import Bool, DateTimeUTC, JsonB
from sqlalchemy import ForeignKey, Index, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.db.models._user import User


class AppStore(StoreModelMixin):
    """Shared Advanced Alchemy key-value store backing ``StoreRateLimiter`` and ephemeral state."""

    __tablename__ = "app_store"


class UserSession(UUIDv7AuditBase):
    """Server-side authenticated browser session record."""

    __tablename__ = "auth_session"
    __table_args__ = (
        Index("ix_auth_session_user_expires", "user_id", "expires_at"),
        {"comment": "Authenticated browser sessions for litestar-security"},
    )

    session_id: Mapped[str] = mapped_column(String(length=128), unique=True, index=True, nullable=False)
    binding_id: Mapped[str] = mapped_column(String(length=128), index=True, nullable=False)
    binding_digest: Mapped[str] = mapped_column(String(length=128), unique=True, index=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_account.id", ondelete="cascade"),
        index=True,
        nullable=False,
    )
    security_epoch: Mapped[int] = mapped_column(Integer, nullable=False)
    authenticated_at: Mapped[datetime] = mapped_column(DateTimeUTC(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTimeUTC(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTimeUTC(timezone=True), index=True, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), nullable=True, default=None)
    display_metadata: Mapped[dict[str, Any] | None] = mapped_column(JsonB, nullable=True, default=None)

    user: Mapped[User] = relationship(back_populates="sessions", lazy="noload")


class PurposeToken(UUIDv7AuditBase):
    """Single-use digest-backed verification and password recovery token."""

    __tablename__ = "auth_purpose_token"
    __table_args__ = (
        Index("ix_auth_purpose_token_user_purpose", "user_id", "purpose"),
        {"comment": "Single-use verification and recovery purpose tokens"},
    )

    token_id: Mapped[str] = mapped_column(String(length=128), unique=True, index=True, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(length=128), unique=True, index=True, nullable=False)
    purpose: Mapped[str] = mapped_column(String(length=64), index=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_account.id", ondelete="cascade"),
        index=True,
        nullable=False,
    )
    issued_security_epoch: Mapped[int] = mapped_column(Integer, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    maximum_attempts: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTimeUTC(timezone=True), index=True, nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), nullable=True, default=None)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), nullable=True, default=None)


class UserMFAFactor(UUIDv7AuditBase):
    """Enrolled or pending TOTP multi-factor authentication record."""

    __tablename__ = "auth_mfa_factor"
    __table_args__ = (
        Index("ix_auth_mfa_factor_user_confirmed", "user_id", "is_confirmed"),
        {"comment": "Pending and confirmed TOTP MFA factors"},
    )

    method_id: Mapped[str] = mapped_column(String(length=128), unique=True, index=True, nullable=False)
    enrollment_id: Mapped[str | None] = mapped_column(
        String(length=128), unique=True, index=True, nullable=True, default=None
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_account.id", ondelete="cascade"),
        index=True,
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(length=32), default="totp", nullable=False)
    secret_ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    key_version: Mapped[str] = mapped_column(String(length=64), nullable=False)
    digits: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    period_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    algorithm: Mapped[str] = mapped_column(String(length=32), default="SHA1", nullable=False)
    allowed_drift_steps: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_accepted_counter: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    is_confirmed: Mapped[bool] = mapped_column(Bool, default=False, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), nullable=True, default=None)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), nullable=True, default=None)

    user: Mapped[User] = relationship(back_populates="mfa_factors", lazy="noload")


class UserMFARecoveryCode(UUIDv7AuditBase):
    """Single-use peppered digest of an MFA recovery code."""

    __tablename__ = "auth_mfa_recovery_code"
    __table_args__ = (
        Index("ix_auth_mfa_recovery_user_digest", "user_id", "digest"),
        {"comment": "Peppered digests for MFA recovery codes"},
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_account.id", ondelete="cascade"),
        index=True,
        nullable=False,
    )
    pepper_version: Mapped[str] = mapped_column(String(length=64), nullable=False)
    digest: Mapped[str] = mapped_column(String(length=128), index=True, nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), nullable=True, default=None)


class MFALoginChallenge(UUIDv7AuditBase):
    """Atomic single-use MFA login challenge."""

    __tablename__ = "auth_mfa_login_challenge"
    __table_args__ = {"comment": "Single-use login MFA challenges"}

    challenge_hash: Mapped[str] = mapped_column(String(length=128), unique=True, index=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_account.id", ondelete="cascade"),
        index=True,
        nullable=False,
    )
    security_epoch: Mapped[int] = mapped_column(Integer, nullable=False)
    client_key: Mapped[str | None] = mapped_column(String(length=255), nullable=True, default=None)
    issued_at: Mapped[datetime] = mapped_column(DateTimeUTC(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTimeUTC(timezone=True), index=True, nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), nullable=True, default=None)


class StepUpGrant(UUIDv7AuditBase):
    """Short-lived step-up authentication assurance grant."""

    __tablename__ = "auth_step_up_grant"
    __table_args__ = {"comment": "Short-lived step-up assurance grants"}

    grant_digest: Mapped[str] = mapped_column(String(length=128), unique=True, index=True, nullable=False)
    transport_digest: Mapped[str] = mapped_column(String(length=128), index=True, nullable=False)
    principal_id: Mapped[str] = mapped_column(String(length=128), index=True, nullable=False)
    security_epoch: Mapped[int] = mapped_column(Integer, nullable=False)
    purpose: Mapped[str] = mapped_column(String(length=128), nullable=False)
    methods: Mapped[list[str]] = mapped_column(JsonB, nullable=False)
    traits: Mapped[list[str]] = mapped_column(JsonB, nullable=False)
    authenticated_at: Mapped[datetime] = mapped_column(DateTimeUTC(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTimeUTC(timezone=True), index=True, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), nullable=True, default=None)


class UserPasskey(UUIDv7AuditBase):
    """WebAuthn passkey credential registered to a user account."""

    __tablename__ = "auth_passkey"
    __table_args__ = {"comment": "Registered WebAuthn passkeys"}

    credential_id: Mapped[str] = mapped_column(String(length=512), unique=True, index=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_account.id", ondelete="cascade"),
        index=True,
        nullable=False,
    )
    public_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    sign_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    backup_eligible: Mapped[bool] = mapped_column(Bool, default=False, nullable=False)
    backup_state: Mapped[bool] = mapped_column(Bool, default=False, nullable=False)
    user_verified: Mapped[bool] = mapped_column(Bool, default=False, nullable=False)
    aaguid: Mapped[str | None] = mapped_column(String(length=64), nullable=True, default=None)
    attestation_format: Mapped[str | None] = mapped_column(String(length=64), nullable=True, default=None)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(length=255), nullable=True, default=None)
    suspect: Mapped[bool] = mapped_column(Bool, default=False, nullable=False)
    hardware_backed: Mapped[bool] = mapped_column(Bool, default=False, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), nullable=True, default=None)

    user: Mapped[User] = relationship(back_populates="passkeys", lazy="noload")


class PasskeyChallenge(UUIDv7AuditBase):
    """Single-use WebAuthn registration or authentication ceremony challenge."""

    __tablename__ = "auth_passkey_challenge"
    __table_args__ = {"comment": "Single-use WebAuthn ceremony challenges"}

    challenge_id: Mapped[str] = mapped_column(String(length=128), unique=True, index=True, nullable=False)
    binding_digest: Mapped[str | None] = mapped_column(String(length=128), nullable=True, default=None)
    purpose: Mapped[str] = mapped_column(String(length=64), nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="cascade"),
        index=True,
        nullable=True,
        default=None,
    )
    rp_id: Mapped[str] = mapped_column(String(length=255), nullable=False)
    origins: Mapped[list[str]] = mapped_column(JsonB, nullable=False)
    user_verification: Mapped[str] = mapped_column(String(length=32), nullable=False)
    algorithms: Mapped[list[int]] = mapped_column(JsonB, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTimeUTC(timezone=True), index=True, nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), nullable=True, default=None)


class OAuthTransaction(UUIDv7AuditBase):
    """Single-use OAuth authorization state with AES-GCM protected PKCE and nonce payload."""

    __tablename__ = "auth_oauth_transaction"
    __table_args__ = {"comment": "Single-use OAuth PKCE transactions"}

    state_hash: Mapped[str] = mapped_column(String(length=128), unique=True, index=True, nullable=False)
    binding_digest: Mapped[str] = mapped_column(String(length=128), index=True, nullable=False)
    operation: Mapped[str] = mapped_column(String(length=32), nullable=False)
    provider: Mapped[str] = mapped_column(String(length=64), nullable=False)
    expected_issuer: Mapped[str | None] = mapped_column(String(length=500), nullable=True, default=None)
    redirect_uri: Mapped[str] = mapped_column(Text, nullable=False)
    return_to: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    requested_scopes: Mapped[list[str]] = mapped_column(JsonB, nullable=False)
    protected_payload: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    key_version: Mapped[str] = mapped_column(String(length=64), nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="cascade"),
        index=True,
        nullable=True,
        default=None,
    )
    session_binding: Mapped[str | None] = mapped_column(String(length=128), nullable=True, default=None)
    security_epoch: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    provider_account_id: Mapped[str | None] = mapped_column(String(length=128), nullable=True, default=None)
    step_up_purpose: Mapped[str | None] = mapped_column(String(length=128), nullable=True, default=None)
    maximum_authentication_age: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    expires_at: Mapped[datetime] = mapped_column(DateTimeUTC(timezone=True), index=True, nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), nullable=True, default=None)


class APIKey(UUIDv7AuditBase):
    """Digest-only API key credential with rotation lineage and usage tracking."""

    __tablename__ = "auth_api_key"
    __table_args__ = (
        Index("ix_auth_api_key_user_revoked", "user_id", "revoked_at"),
        {"comment": "Self-service API keys for machine and MCP authentication"},
    )

    key_id: Mapped[str] = mapped_column(String(length=128), unique=True, index=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_account.id", ondelete="cascade"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(length=120), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(length=32), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(length=128), unique=True, index=True, nullable=False)
    scopes: Mapped[list[str]] = mapped_column(JsonB, default=list, nullable=False)
    restrictions: Mapped[dict[str, Any] | None] = mapped_column(JsonB, nullable=True, default=None)
    rotated_from_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("auth_api_key.id", ondelete="set null"),
        nullable=True,
        default=None,
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), index=True, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), nullable=True, default=None)
    overlap_until: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), nullable=True, default=None)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), nullable=True, default=None)

    user: Mapped[User] = relationship(back_populates="api_keys", lazy="noload")
