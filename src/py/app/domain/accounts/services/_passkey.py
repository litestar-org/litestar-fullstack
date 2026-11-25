"""WebAuthn passkey credential and ceremony challenge database services."""

from __future__ import annotations

from base64 import urlsafe_b64decode, urlsafe_b64encode
from hmac import compare_digest
from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy.extensions.litestar import service
from litestar_security.accounts import LoginMethod, PasskeyCredential, UserVerification, WebAuthnChallenge
from sqlalchemy import update

from app.db import models as m
from app.domain.accounts.services._statements import affected_rows
from app.domain.accounts.services._user import UserService

if TYPE_CHECKING:
    from datetime import datetime

    from advanced_alchemy.service import ModelDictT

_LOGIN_METHOD_PREFIX = "pk_"


class PasskeyService(service.SQLAlchemyAsyncRepositoryService[m.UserPasskey]):
    """Handles database operations for WebAuthn passkey credentials."""

    async def to_model_on_create(self, data: ModelDictT[m.UserPasskey]) -> ModelDictT[m.UserPasskey]:
        """Translate a ``PasskeyCredential`` into the passkey stored for its account.

        Returns:
            The passkey to persist, or ``data`` unchanged when it is not a ``PasskeyCredential``.
        """
        if not isinstance(data, PasskeyCredential):
            return data
        return m.UserPasskey(
            credential_id=data.credential_id.hex(),
            user_id=UUID(data.account_id),
            public_key=data.public_key,
            sign_count=data.sign_count,
            backup_eligible=data.backup_eligible,
            backup_state=data.backup_state,
            user_verified=data.user_verified,
            aaguid=data.aaguid,
            attestation_format=data.attestation_format,
            version=data.version,
            display_name=data.display_name,
            suspect=data.suspect,
            hardware_backed=data.hardware_backed,
            created_at=data.created_at,
            updated_at=data.created_at,
            last_used_at=data.last_used_at,
        )

    @staticmethod
    def to_credential(passkey: m.UserPasskey) -> PasskeyCredential:
        """Translate a stored passkey into the ``PasskeyCredential`` the security library verifies against.

        Returns:
            Credential carrying the stored public key, counters, and flags.
        """
        return PasskeyCredential(
            credential_id=bytes.fromhex(passkey.credential_id),
            account_id=str(passkey.user_id),
            public_key=passkey.public_key,
            sign_count=passkey.sign_count,
            backup_eligible=passkey.backup_eligible,
            backup_state=passkey.backup_state,
            user_verified=passkey.user_verified,
            aaguid=passkey.aaguid or "",
            attestation_format=passkey.attestation_format or "none",
            created_at=passkey.created_at,
            version=passkey.version,
            display_name=passkey.display_name,
            suspect=passkey.suspect,
            last_used_at=passkey.last_used_at,
            hardware_backed=passkey.hardware_backed,
        )

    @staticmethod
    def to_login_method(passkey: m.UserPasskey) -> LoginMethod:
        """Describe a passkey as a ``LoginMethod`` identified by its encoded credential identifier.

        Returns:
            Passkey login method carrying the credential's display name.
        """
        credential_id = urlsafe_b64encode(bytes.fromhex(passkey.credential_id)).rstrip(b"=").decode("ascii")
        return LoginMethod(
            method_id=f"{_LOGIN_METHOD_PREFIX}{credential_id}",
            kind="passkey",
            created_at=passkey.created_at,
            display_name=passkey.display_name,
        )

    async def find_for_login_method(self, user_id: UUID, method_id: str) -> m.UserPasskey | None:
        """Load the passkey a login method identifier names, when ``user_id`` owns it.

        Returns:
            The passkey, or ``None`` when ``method_id`` does not name one of the user's passkeys.
        """
        credential_id = self._to_credential_id(method_id)
        if credential_id is None:
            return None
        return await self.get_one_or_none(
            m.UserPasskey.user_id == user_id,
            m.UserPasskey.credential_id == credential_id,
        )

    async def record_assertion(
        self,
        passkey: m.UserPasskey,
        *,
        expected_version: int,
        sign_count: int,
        backup_eligible: bool,
        backup_state: bool,
        clone_risk: bool,
        now: datetime,
    ) -> bool:
        """Advance the signature counter only while the stored version still equals ``expected_version``.

        Returns:
            ``True`` when the passkey was updated, ``False`` when another assertion won the race.
        """
        statement = (
            update(m.UserPasskey)
            .where(m.UserPasskey.id == passkey.id, m.UserPasskey.version == expected_version)
            .values(
                version=expected_version + 1,
                sign_count=max(passkey.sign_count, sign_count),
                backup_eligible=backup_eligible,
                backup_state=backup_state,
                suspect=passkey.suspect or clone_risk,
                last_used_at=now,
            )
        )
        return await affected_rows(self.repository.session, statement) == 1

    @staticmethod
    def _to_credential_id(method_id: str) -> str | None:
        if not method_id.startswith(_LOGIN_METHOD_PREFIX):
            return None
        encoded_credential_id = method_id.removeprefix(_LOGIN_METHOD_PREFIX)
        padding = "=" * (-len(encoded_credential_id) % 4)
        try:
            return urlsafe_b64decode(f"{encoded_credential_id}{padding}".encode("ascii")).hex()
        except ValueError:
            return None


class PasskeyChallengeService(service.SQLAlchemyAsyncRepositoryService[m.PasskeyChallenge]):
    """Handles database operations for single-use WebAuthn ceremony challenges."""

    async def to_model_on_create(self, data: ModelDictT[m.PasskeyChallenge]) -> ModelDictT[m.PasskeyChallenge]:
        """Translate a ``WebAuthnChallenge`` into the stored ceremony challenge.

        Returns:
            The challenge to persist, or ``data`` unchanged when it is not a ``WebAuthnChallenge``.
        """
        if not isinstance(data, WebAuthnChallenge):
            return data
        return m.PasskeyChallenge(
            challenge_id=data.challenge_digest.hex(),
            binding_digest=data.binding_digest.hex(),
            purpose=data.purpose,
            user_id=UserService.to_user_id(data.account_id),
            rp_id=data.rp_id,
            origins=list(data.origins),
            user_verification=data.user_verification.value,
            algorithms=list(data.algorithms),
            expires_at=data.expires_at,
        )

    async def redeem(
        self,
        challenge_digest: bytes,
        *,
        binding_digest: bytes,
        purpose: str,
        now: datetime,
    ) -> WebAuthnChallenge | None:
        """Burn an unconsumed challenge and hand it back only when it was issued for this ceremony.

        The challenge is burned whenever it is found, so a wrong binding, purpose, or an expired
        challenge cannot be presented a second time.

        Returns:
            The challenge when this call burned it and binding, purpose, and expiry all match, otherwise ``None``.
        """
        passkey_challenge = await self.get_one_or_none(
            m.PasskeyChallenge.challenge_id == challenge_digest.hex(),
            m.PasskeyChallenge.consumed_at.is_(None),
        )
        if passkey_challenge is None or not await self._burn(passkey_challenge, now=now):
            return None
        issued_for_ceremony = (
            passkey_challenge.binding_digest is not None
            and compare_digest(bytes.fromhex(passkey_challenge.binding_digest), binding_digest)
            and passkey_challenge.purpose == purpose
            and passkey_challenge.expires_at > now
        )
        return self._to_webauthn_challenge(passkey_challenge, binding_digest) if issued_for_ceremony else None

    async def _burn(self, passkey_challenge: m.PasskeyChallenge, *, now: datetime) -> bool:
        statement = (
            update(m.PasskeyChallenge)
            .where(m.PasskeyChallenge.id == passkey_challenge.id, m.PasskeyChallenge.consumed_at.is_(None))
            .values(consumed_at=now)
        )
        return await affected_rows(self.repository.session, statement) == 1

    @staticmethod
    def _to_webauthn_challenge(passkey_challenge: m.PasskeyChallenge, binding_digest: bytes) -> WebAuthnChallenge:
        return WebAuthnChallenge(
            challenge_digest=bytes.fromhex(passkey_challenge.challenge_id),
            binding_digest=binding_digest,
            purpose=passkey_challenge.purpose,
            account_id=str(passkey_challenge.user_id) if passkey_challenge.user_id is not None else None,
            rp_id=passkey_challenge.rp_id,
            origins=tuple(passkey_challenge.origins),
            user_verification=UserVerification(passkey_challenge.user_verification),
            algorithms=tuple(passkey_challenge.algorithms),
            expires_at=passkey_challenge.expires_at,
        )
