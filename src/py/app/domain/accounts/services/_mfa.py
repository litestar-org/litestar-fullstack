"""TOTP factor, recovery code, login challenge, and step-up grant database services."""

from __future__ import annotations

from hmac import compare_digest
from typing import TYPE_CHECKING, Literal, cast
from uuid import UUID

from advanced_alchemy.extensions.litestar import service
from litestar_security.accounts import (
    LoginMethod,
    MFALoginChallenge,
    PendingTOTPEnrollment,
    ProtectedSecret,
    StepUpGrantState,
    TOTPMethod,
    TOTPPolicy,
)
from sqlalchemy import false, or_, true, update

from app.db import models as m
from app.domain.accounts.services._statements import affected_rows
from app.domain.accounts.services._user import UserService

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from advanced_alchemy.service import ModelDictT
    from litestar_security.accounts import RecoveryCodeDigest

_TOTP_LONG_DIGITS = 8


class MFAFactorService(service.SQLAlchemyAsyncRepositoryService[m.UserMFAFactor]):
    """Handles database operations for TOTP factors and pending enrollments."""

    async def to_model_on_create(self, data: ModelDictT[m.UserMFAFactor]) -> ModelDictT[m.UserMFAFactor]:
        """Translate a ``PendingTOTPEnrollment`` into the unconfirmed factor stored for its account.

        Returns:
            The factor to persist, or ``data`` unchanged when it is not a ``PendingTOTPEnrollment``.
        """
        if not isinstance(data, PendingTOTPEnrollment):
            return data
        return m.UserMFAFactor(
            method_id=data.method_id,
            enrollment_id=data.enrollment_id,
            user_id=UUID(data.account_id),
            kind="totp",
            secret_ciphertext=data.protected_secret.ciphertext,
            key_version=data.protected_secret.key_version,
            digits=data.policy.digits,
            period_seconds=data.policy.period_seconds,
            algorithm=data.policy.algorithm,
            allowed_drift_steps=data.policy.allowed_drift_steps,
            is_confirmed=False,
            created_at=data.created_at,
            updated_at=data.created_at,
            expires_at=data.expires_at,
        )

    def to_enrollment(self, mfa_factor: m.UserMFAFactor) -> PendingTOTPEnrollment | None:
        """Translate a pending factor into the ``PendingTOTPEnrollment`` it was created from.

        Returns:
            The pending enrollment, or ``None`` when the factor no longer carries enrollment details.
        """
        if mfa_factor.enrollment_id is None or mfa_factor.expires_at is None:
            return None
        return PendingTOTPEnrollment(
            enrollment_id=mfa_factor.enrollment_id,
            method_id=mfa_factor.method_id,
            account_id=str(mfa_factor.user_id),
            protected_secret=ProtectedSecret(
                ciphertext=mfa_factor.secret_ciphertext, key_version=mfa_factor.key_version
            ),
            policy=self._to_totp_policy(mfa_factor),
            created_at=mfa_factor.created_at,
            expires_at=mfa_factor.expires_at,
        )

    def to_totp_method(self, mfa_factor: m.UserMFAFactor) -> TOTPMethod:
        """Translate a confirmed factor into the ``TOTPMethod`` the security library verifies codes against.

        Returns:
            The TOTP method, reporting a counter of ``-1`` until a code has been accepted.
        """
        return TOTPMethod(
            method_id=mfa_factor.method_id,
            account_id=str(mfa_factor.user_id),
            protected_secret=ProtectedSecret(
                ciphertext=mfa_factor.secret_ciphertext, key_version=mfa_factor.key_version
            ),
            policy=self._to_totp_policy(mfa_factor),
            last_accepted_counter=(
                mfa_factor.last_accepted_counter if mfa_factor.last_accepted_counter is not None else -1
            ),
            created_at=mfa_factor.created_at,
            last_used_at=mfa_factor.last_used_at,
        )

    @staticmethod
    def to_login_method(mfa_factor: m.UserMFAFactor) -> LoginMethod:
        """Describe a confirmed factor as a ``LoginMethod``.

        Returns:
            Login method carrying the factor's identifier and kind.
        """
        return LoginMethod(method_id=mfa_factor.method_id, kind=mfa_factor.kind, created_at=mfa_factor.created_at)

    async def find_pending(self, enrollment_id: str) -> m.UserMFAFactor | None:
        """Load the unconfirmed enrollment with this identifier.

        Returns:
            The pending factor, or ``None`` when it is unknown or already confirmed.
        """
        return await self.get_one_or_none(
            m.UserMFAFactor.enrollment_id == enrollment_id,
            m.UserMFAFactor.is_confirmed.is_(false()),
        )

    async def find_active(self, user_id: UUID, method_id: str) -> m.UserMFAFactor | None:
        """Load a confirmed factor owned by ``user_id``.

        Returns:
            The active factor, or ``None`` when it is unknown, pending, or owned by another account.
        """
        return await self.get_one_or_none(
            m.UserMFAFactor.user_id == user_id,
            m.UserMFAFactor.method_id == method_id,
            m.UserMFAFactor.is_confirmed.is_(true()),
        )

    async def list_active(self, user_id: UUID) -> Sequence[m.UserMFAFactor]:
        """List the confirmed factors owned by ``user_id``.

        Returns:
            Active factors the account can sign in with.
        """
        return await self.list(m.UserMFAFactor.user_id == user_id, m.UserMFAFactor.is_confirmed.is_(true()))

    async def confirm_enrollment(self, mfa_factor: m.UserMFAFactor, *, accepted_counter: int, now: datetime) -> bool:
        """Turn an unexpired pending enrollment into an active factor, updating the loaded ``mfa_factor`` to match.

        Returns:
            ``True`` when this call confirmed the enrollment, ``False`` when it expired or was already confirmed.
        """
        statement = (
            update(m.UserMFAFactor)
            .where(
                m.UserMFAFactor.id == mfa_factor.id,
                m.UserMFAFactor.is_confirmed.is_(false()),
                or_(m.UserMFAFactor.expires_at.is_(None), m.UserMFAFactor.expires_at > now),
            )
            .values(
                is_confirmed=True,
                enrollment_id=None,
                expires_at=None,
                last_accepted_counter=accepted_counter,
                last_used_at=now,
            )
        )
        return await affected_rows(self.repository.session, statement) == 1

    async def advance_counter(self, method_id: str, *, accepted_counter: int, now: datetime) -> bool:
        """Advance an active factor's counter only to a strictly greater value.

        Returns:
            ``True`` when the counter advanced, ``False`` when the code was already used or the factor is not active.
        """
        statement = (
            update(m.UserMFAFactor)
            .where(
                m.UserMFAFactor.method_id == method_id,
                m.UserMFAFactor.is_confirmed.is_(true()),
                or_(
                    m.UserMFAFactor.last_accepted_counter.is_(None),
                    m.UserMFAFactor.last_accepted_counter < accepted_counter,
                ),
            )
            .values(last_accepted_counter=accepted_counter, last_used_at=now)
        )
        return await affected_rows(self.repository.session, statement) == 1

    @staticmethod
    def _to_totp_policy(mfa_factor: m.UserMFAFactor) -> TOTPPolicy:
        digits: Literal[6, 8] = 8 if mfa_factor.digits == _TOTP_LONG_DIGITS else 6
        return TOTPPolicy(
            digits=digits,
            period_seconds=mfa_factor.period_seconds,
            algorithm=cast("Literal['SHA1', 'SHA256', 'SHA512']", mfa_factor.algorithm),
            allowed_drift_steps=mfa_factor.allowed_drift_steps,
        )


class MFARecoveryCodeService(service.SQLAlchemyAsyncRepositoryService[m.UserMFARecoveryCode]):
    """Handles database operations for single-use MFA recovery codes."""

    async def replace_all(self, user_id: UUID, codes: Sequence[RecoveryCodeDigest]) -> None:
        """Swap an account's complete recovery code set, skipping digests issued for another account."""
        await self.delete_where(m.UserMFARecoveryCode.user_id == user_id, sanity_check=False)
        await self.create_many(
            [
                m.UserMFARecoveryCode(user_id=user_id, pepper_version=code.pepper_version, digest=code.digest.hex())
                for code in codes
                if UserService.to_user_id(code.account_id) == user_id
            ]
        )

    async def burn(self, user_id: UUID, digest: bytes, *, now: datetime) -> bool:
        """Mark one unused recovery code as consumed.

        Returns:
            ``True`` when this call consumed the code, ``False`` when it is unknown or already consumed.
        """
        statement = (
            update(m.UserMFARecoveryCode)
            .where(
                m.UserMFARecoveryCode.user_id == user_id,
                m.UserMFARecoveryCode.digest == digest.hex(),
                m.UserMFARecoveryCode.consumed_at.is_(None),
            )
            .values(consumed_at=now)
        )
        return await affected_rows(self.repository.session, statement) == 1


class MFALoginChallengeService(service.SQLAlchemyAsyncRepositoryService[m.MFALoginChallenge]):
    """Handles database operations for single-use MFA login challenges."""

    async def to_model_on_create(self, data: ModelDictT[m.MFALoginChallenge]) -> ModelDictT[m.MFALoginChallenge]:
        """Translate an ``MFALoginChallenge`` into the login challenge stored for its account.

        Returns:
            The login challenge to persist, or ``data`` unchanged when it is not an ``MFALoginChallenge``.
        """
        if not isinstance(data, MFALoginChallenge):
            return data
        return m.MFALoginChallenge(
            challenge_hash=data.challenge_digest.hex(),
            user_id=UUID(data.account_id),
            security_epoch=data.security_epoch,
            client_key=data.client_key,
            issued_at=data.issued_at,
            expires_at=data.expires_at,
        )

    async def redeem(
        self,
        challenge_digest: bytes,
        *,
        account_id: str,
        security_epoch: int,
        now: datetime,
    ) -> MFALoginChallenge | None:
        """Burn an unconsumed login challenge and hand it back only when it was issued for this login.

        The login challenge is burned whenever it is found, so a wrong account, a stale epoch, or an expired
        challenge cannot be presented a second time.

        Returns:
            The challenge when this call burned it and account, epoch, and expiry all match, otherwise ``None``.
        """
        login_challenge = await self.get_one_or_none(
            m.MFALoginChallenge.challenge_hash == challenge_digest.hex(),
            m.MFALoginChallenge.consumed_at.is_(None),
        )
        if login_challenge is None or not await self._burn(login_challenge, now=now):
            return None
        issued_for_login = (
            str(login_challenge.user_id) == account_id
            and login_challenge.security_epoch == security_epoch
            and login_challenge.expires_at > now
        )
        return self._to_login_challenge(login_challenge) if issued_for_login else None

    async def _burn(self, login_challenge: m.MFALoginChallenge, *, now: datetime) -> bool:
        statement = (
            update(m.MFALoginChallenge)
            .where(m.MFALoginChallenge.id == login_challenge.id, m.MFALoginChallenge.consumed_at.is_(None))
            .values(consumed_at=now)
        )
        return await affected_rows(self.repository.session, statement) == 1

    @staticmethod
    def _to_login_challenge(login_challenge: m.MFALoginChallenge) -> MFALoginChallenge:
        return MFALoginChallenge(
            challenge_digest=bytes.fromhex(login_challenge.challenge_hash),
            account_id=str(login_challenge.user_id),
            security_epoch=login_challenge.security_epoch,
            client_key=login_challenge.client_key,
            issued_at=login_challenge.issued_at,
            expires_at=login_challenge.expires_at,
        )


class StepUpGrantService(service.SQLAlchemyAsyncRepositoryService[m.StepUpGrant]):
    """Handles database operations for single-use step-up grants."""

    async def to_model_on_create(self, data: ModelDictT[m.StepUpGrant]) -> ModelDictT[m.StepUpGrant]:
        """Translate a ``StepUpGrantState`` into the stored step-up grant.

        Returns:
            The step-up grant to persist, or ``data`` unchanged when it is not a ``StepUpGrantState``.
        """
        if not isinstance(data, StepUpGrantState):
            return data
        return m.StepUpGrant(
            grant_digest=data.grant_digest.hex(),
            transport_digest=data.transport_digest.hex(),
            principal_id=data.principal_id,
            security_epoch=data.security_epoch,
            purpose=data.purpose,
            methods=sorted(data.methods),
            traits=sorted(data.traits),
            authenticated_at=data.authenticated_at,
            expires_at=data.expires_at,
        )

    async def redeem(
        self,
        grant_digest: bytes,
        *,
        principal_id: str,
        security_epoch: int,
        purpose: str,
        transport_digest: bytes,
        now: datetime,
    ) -> StepUpGrantState | None:
        """Burn an unspent step-up grant only when it was granted for this request.

        A request with a wrong principal, epoch, purpose, or transport, or one arriving after expiry, leaves
        the step-up grant unspent.

        Returns:
            The grant when every binding matches and this call burned it, otherwise ``None``.
        """
        step_up_grant = await self.get_one_or_none(
            m.StepUpGrant.grant_digest == grant_digest.hex(),
            m.StepUpGrant.revoked_at.is_(None),
        )
        if step_up_grant is None:
            return None
        granted_for_request = (
            step_up_grant.principal_id == principal_id
            and step_up_grant.security_epoch == security_epoch
            and step_up_grant.purpose == purpose
            and compare_digest(bytes.fromhex(step_up_grant.transport_digest), transport_digest)
            and step_up_grant.expires_at > now
        )
        if not granted_for_request or not await self._burn(step_up_grant, now=now):
            return None
        return self._to_grant_state(step_up_grant)

    async def _burn(self, step_up_grant: m.StepUpGrant, *, now: datetime) -> bool:
        statement = (
            update(m.StepUpGrant)
            .where(m.StepUpGrant.id == step_up_grant.id, m.StepUpGrant.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        return await affected_rows(self.repository.session, statement) == 1

    @staticmethod
    def _to_grant_state(step_up_grant: m.StepUpGrant) -> StepUpGrantState:
        return StepUpGrantState(
            grant_digest=bytes.fromhex(step_up_grant.grant_digest),
            transport_digest=bytes.fromhex(step_up_grant.transport_digest),
            principal_id=step_up_grant.principal_id,
            security_epoch=step_up_grant.security_epoch,
            purpose=step_up_grant.purpose,
            methods=frozenset(step_up_grant.methods),
            traits=frozenset(step_up_grant.traits),
            authenticated_at=step_up_grant.authenticated_at,
            expires_at=step_up_grant.expires_at,
        )
