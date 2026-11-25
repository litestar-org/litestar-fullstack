"""Service groups sharing one SQLAlchemy AsyncSession per unit of work."""

from collections.abc import Sequence
from datetime import UTC, datetime
from hmac import compare_digest
from uuid import UUID

from advanced_alchemy.exceptions import IntegrityError
from advanced_alchemy.service import ServiceGroup
from litestar.exceptions import HTTPException
from litestar_security.accounts import (
    LoginMethod,
    RecoveryCodeDigest,
    RegistrationCommand,
    RegistrationStatus,
    RevokeLoginMethodStatus,
    TokenPurpose,
    normalize_identifier,
)
from litestar_security.providers.oauth import (
    AccountLinkError,
    OAuthLoginOutcome,
    ProtectedOAuthSecret,
    ProviderGrant,
    ProviderIdentity,
    UnlinkStatus,
)

from app.db import models as m
from app.domain.accounts.services._api_key import APIKeyRecordService
from app.domain.accounts.services._mfa import (
    MFAFactorService,
    MFALoginChallengeService,
    MFARecoveryCodeService,
    StepUpGrantService,
)
from app.domain.accounts.services._oauth import OAuthAccountService, OAuthTransactionService
from app.domain.accounts.services._passkey import PasskeyChallengeService, PasskeyService
from app.domain.accounts.services._role import RoleService
from app.domain.accounts.services._session import (
    LoginMethodService,
    PurposeTokenService,
    TokenRejection,
    UserSessionService,
)
from app.domain.accounts.services._statements import is_constraint_violation
from app.domain.accounts.services._user import UserService
from app.domain.accounts.services._user_role import UserRoleService
from app.domain.admin.services._audit import AuditLogService

__all__ = (
    "APIKeyServices",
    "AccountSecurityServices",
    "AccountServices",
    "MFAServices",
    "OAuthServices",
    "PasskeyServices",
)


class AccountServices(ServiceGroup):
    """Coordinated accounts and audit services sharing one ``AsyncSession``."""

    users: UserService
    roles: RoleService
    user_roles: UserRoleService
    audit_logs: AuditLogService

    async def assign_role(self, role_slug: str, *, email: str, actor: m.User) -> None:
        """Give a user a role and record who assigned it, in one transaction.

        Raises:
            HTTPException: If the role or user does not exist, or the user already holds the role.
        """
        role, user = await self._find_role_and_user(role_slug, email)
        if await self.user_roles.exists(user_id=user.id, role_id=role.id):
            raise HTTPException(status_code=409, detail=f"User '{email}' already has role '{role_slug}'")
        await self.user_roles.create({"user_id": user.id, "role_id": role.id, "assigned_at": datetime.now(UTC)})
        await self._record_role_change("role.assigned", role_slug, user=user, actor=actor)

    async def revoke_role(self, role_slug: str, *, email: str, actor: m.User) -> None:
        """Take a role away from a user and record who revoked it, in one transaction.

        Raises:
            HTTPException: If the role or user does not exist, or the user does not hold the role.
        """
        role, user = await self._find_role_and_user(role_slug, email)
        user_role = await self.user_roles.get_one_or_none(user_id=user.id, role_id=role.id)
        if user_role is None:
            raise HTTPException(status_code=404, detail=f"User '{email}' does not have role '{role_slug}'")
        await self.user_roles.delete(user_role.id)
        await self._record_role_change("role.revoked", role_slug, user=user, actor=actor)

    async def _find_role_and_user(self, role_slug: str, email: str) -> tuple[m.Role, m.User]:
        role = await self.roles.get_one_or_none(slug=role_slug)
        if role is None:
            raise HTTPException(status_code=404, detail=f"Role '{role_slug}' not found")
        user = await self.users.get_one_or_none(email=email)
        if user is None:
            raise HTTPException(status_code=404, detail=f"User '{email}' not found")
        return role, user

    async def _record_role_change(self, action: str, role_slug: str, *, user: m.User, actor: m.User) -> None:
        await self.audit_logs.log_action(
            action=action,
            actor_id=actor.id,
            actor_email=actor.email,
            target_type="user",
            target_id=str(user.id),
            target_label=user.email,
            details={"role_slug": role_slug},
        )
        await self.session.commit()


class AccountSecurityServices(ServiceGroup):
    """Services behind local accounts, purpose tokens, login methods, and browser sessions."""

    users: UserService
    roles: RoleService
    user_roles: UserRoleService
    user_sessions: UserSessionService
    purpose_tokens: PurposeTokenService
    login_methods: LoginMethodService
    mfa_factors: MFAFactorService
    passkeys: PasskeyService
    oauth_accounts: OAuthAccountService
    audit_logs: AuditLogService

    async def register_account(
        self,
        command: RegistrationCommand,
        password_hash: str,
        *,
        invitation_digest: bytes | None,
        verified: bool,
        now: datetime,
    ) -> m.User | RegistrationStatus:
        """Provision the account a registration asks for, redeeming its invitation first.

        Args:
            command: Normalized identifier and display name to register.
            password_hash: Argon2 hash of the chosen password.
            invitation_digest: Digest of the invitation the registration presents, when one is required.
            verified: Whether the account starts with a confirmed email address.
            now: Timestamp of the registration.

        Returns:
            The provisioned user, or the status rejecting the registration: ``DUPLICATE`` when the identifier
            is taken, ``INVALID_INVITATION`` when the invitation cannot be redeemed.

        Raises:
            IntegrityError: If the database fails for a reason other than a violated constraint.
        """
        if await self.users.exists(email=command.normalized_identifier):
            return RegistrationStatus.DUPLICATE
        if invitation_digest is not None:
            invitation_redeemed = await self.purpose_tokens.redeem_invitation(invitation_digest, now=now)
            if not invitation_redeemed:
                return RegistrationStatus.INVALID_INVITATION
        try:
            return await self.users.provision(
                email=command.normalized_identifier,
                name=command.display_name,
                verified=verified,
                now=now,
                hashed_password=password_hash,
            )
        except IntegrityError as error:
            if not is_constraint_violation(error):
                raise
            return RegistrationStatus.DUPLICATE

    async def redeem_purpose_token(
        self,
        token_id: str,
        digest: bytes,
        *,
        purpose: TokenPurpose,
        now: datetime,
    ) -> m.User | TokenRejection:
        """Burn a verification or recovery token and hand back the account it was issued to.

        A wrong ``digest`` counts against the token's attempts and commits immediately, so the failed attempt
        survives whatever the caller does next. A recovery token is honoured only while the account's security
        epoch still equals the epoch it was issued at.

        Returns:
            The token's user when this call burned the token, otherwise why it was rejected.
        """
        purpose_token = await self.purpose_tokens.get_one_or_none(m.PurposeToken.token_id == token_id)
        if purpose_token is None or purpose_token.purpose != purpose.value:
            return "invalid"
        if purpose_token.consumed_at is not None or purpose_token.revoked_at is not None:
            return "used"
        if not compare_digest(bytes.fromhex(purpose_token.token_hash), digest):
            await self.purpose_tokens.record_failed_attempt(purpose_token, now=now)
            await self.session.commit()
            return "invalid"
        if purpose_token.expires_at <= now:
            return "expired"

        user = None
        if purpose_token.user_id is not None:
            user = await self.users.get_one_or_none(m.User.id == purpose_token.user_id)
        issued_before_epoch_bump = (
            purpose is TokenPurpose.RECOVERY
            and user is not None
            and user.security_epoch != purpose_token.issued_security_epoch
        )
        if user is None or issued_before_epoch_bump:
            return "conflict"
        burned = await self.purpose_tokens.burn(purpose_token, now=now)
        return user if burned else "used"

    async def list_login_methods(self, account_id: str) -> tuple[LoginMethod, ...]:
        """List every way the account can sign in: recorded methods, its password, MFA factors, and passkeys.

        Returns:
            The account's login methods, recorded ones first.
        """
        user_id = self.users.to_user_id(account_id)
        user = await self.users.find_with_password(user_id) if user_id is not None else None
        return tuple((await self._login_methods(account_id, user)).values())

    async def revoke_login_method(
        self,
        account_id: str,
        method_id: str,
        *,
        require_remaining: bool,
    ) -> RevokeLoginMethodStatus:
        """Remove one of the account's login methods together with the MFA factor or passkey behind it.

        The account stays locked for the transaction, so concurrent revocations cannot each remove a
        different method and leave the account without any.

        Returns:
            ``REVOKED``, ``NOT_FOUND`` when the account has no such method, or ``FINAL_METHOD`` when
            ``require_remaining`` is set and no other login method or linked provider would remain.
        """
        user_id = self.users.to_user_id(account_id)
        user = await self.users.find_for_update(user_id) if user_id is not None else None
        login_methods = await self._login_methods(account_id, user)
        recorded_method = await self.login_methods.find_recorded(account_id, method_id)
        mfa_factor = passkey = None
        linked_provider_count = 0
        if user is not None:
            mfa_factor = await self.mfa_factors.find_active(user.id, method_id)
            passkey = await self.passkeys.find_for_login_method(user.id, method_id)
            linked_provider_count = await self.oauth_accounts.count(m.UserOAuthAccount.user_id == user.id)

        if recorded_method is None and mfa_factor is None and passkey is None:
            return RevokeLoginMethodStatus.NOT_FOUND
        if require_remaining and len(login_methods) + linked_provider_count <= 1:
            return RevokeLoginMethodStatus.FINAL_METHOD

        if recorded_method is not None:
            await self.login_methods.delete(recorded_method.id)
        if mfa_factor is not None:
            await self.mfa_factors.delete(mfa_factor.id)
        if passkey is not None:
            await self.passkeys.delete(passkey.id)
        return RevokeLoginMethodStatus.REVOKED

    async def _login_methods(self, account_id: str, user: m.User | None) -> dict[str, LoginMethod]:
        recorded_methods = [
            self.login_methods.to_login_method(recorded_method)
            for recorded_method in await self.login_methods.list_for_account(account_id)
        ]
        login_methods = {login_method.method_id: login_method for login_method in recorded_methods}
        if user is None:
            return login_methods

        password_is_recorded = any(login_method.kind == "password" for login_method in recorded_methods)
        if user.hashed_password is not None and not password_is_recorded:
            login_methods["password"] = self.users.to_login_method(user)
        for mfa_factor in await self.mfa_factors.list_active(user.id):
            login_methods.setdefault(mfa_factor.method_id, self.mfa_factors.to_login_method(mfa_factor))
        for passkey in await self.passkeys.list(m.UserPasskey.user_id == user.id):
            passkey_method = self.passkeys.to_login_method(passkey)
            login_methods.setdefault(passkey_method.method_id, passkey_method)
        return login_methods


class MFAServices(ServiceGroup):
    """Services behind TOTP factors, recovery codes, login challenges, and step-up grants."""

    users: UserService
    mfa_factors: MFAFactorService
    recovery_codes: MFARecoveryCodeService
    login_challenges: MFALoginChallengeService
    step_up_grants: StepUpGrantService
    login_methods: LoginMethodService
    audit_logs: AuditLogService

    async def activate_totp(
        self,
        user_id: UUID,
        enrollment_id: str,
        *,
        accepted_counter: int,
        login_method: LoginMethod,
        codes: Sequence[RecoveryCodeDigest] | None,
        now: datetime,
    ) -> m.UserMFAFactor | None:
        """Confirm the user's pending TOTP enrollment and record it as a login method.

        Args:
            user_id: Account confirming the enrollment.
            enrollment_id: Pending enrollment being confirmed.
            accepted_counter: TOTP counter of the code that proved possession of the secret.
            login_method: Login method to record for the activated factor.
            codes: Recovery codes replacing the account's current set, or ``None`` to leave them untouched.
            now: Timestamp of the confirmation.

        Returns:
            The activated factor, or ``None`` when the enrollment is unknown, owned by another account,
            expired, or already confirmed.
        """
        mfa_factor = await self.mfa_factors.find_pending(enrollment_id)
        if mfa_factor is None or mfa_factor.user_id != user_id:
            return None
        if not await self.mfa_factors.confirm_enrollment(mfa_factor, accepted_counter=accepted_counter, now=now):
            return None
        await self.login_methods.record(str(user_id), login_method)
        if codes is not None:
            await self.replace_recovery_codes(user_id, codes)
        return mfa_factor

    async def replace_recovery_codes(self, user_id: UUID, codes: Sequence[RecoveryCodeDigest]) -> None:
        """Swap the account's recovery codes while holding its row lock.

        The lock makes concurrent replacements run one at a time, so the account always ends up with exactly
        one caller's complete set.
        """
        await self.users.find_for_update(user_id)
        await self.recovery_codes.replace_all(user_id, codes)


class PasskeyServices(ServiceGroup):
    """Services behind WebAuthn credentials and ceremony challenges."""

    passkeys: PasskeyService
    passkey_challenges: PasskeyChallengeService
    login_methods: LoginMethodService
    audit_logs: AuditLogService


class OAuthServices(ServiceGroup):
    """Services behind linked provider accounts and OAuth transactions."""

    users: UserService
    roles: RoleService
    user_roles: UserRoleService
    oauth_accounts: OAuthAccountService
    oauth_transactions: OAuthTransactionService
    passkeys: PasskeyService

    async def login(
        self,
        identity: ProviderIdentity,
        *,
        grant: ProviderGrant,
        protected_tokens: ProtectedOAuthSecret | None,
        provision_unknown: bool,
        now: datetime,
    ) -> OAuthLoginOutcome:
        """Sign in the account linked to a provider identity, provisioning one first when allowed.

        Args:
            identity: Provider identity that completed the exchange.
            grant: Scopes and expiry the provider granted.
            protected_tokens: Encrypted tokens to retain, or ``None`` to retain none.
            provision_unknown: Whether an identity nobody has linked yet gets a new account.
            now: Timestamp of the provider exchange.

        Returns:
            The linked account and whether this call provisioned its user.

        Raises:
            AccountLinkError: If the identity is unknown and may not be provisioned, or provisioning collides
                with an existing account.
        """
        oauth_account = await self.oauth_accounts.find_by_identity(identity)
        if oauth_account is not None:
            await self.oauth_accounts.replace_grant(
                oauth_account,
                grant=grant,
                protected_tokens=protected_tokens,
                now=now,
                advance_version=False,
            )
            return OAuthLoginOutcome(linked=self.oauth_accounts.to_linked_account(oauth_account), provisioned=False)
        if not provision_unknown:
            raise AccountLinkError
        oauth_account = await self._provision_account(identity, grant=grant, protected_tokens=protected_tokens, now=now)
        return OAuthLoginOutcome(linked=self.oauth_accounts.to_linked_account(oauth_account), provisioned=True)

    async def unlink(
        self,
        user_id: UUID,
        oauth_account_id: UUID,
        provider: str,
        *,
        require_remaining: bool,
    ) -> UnlinkStatus:
        """Remove one of the user's linked provider accounts.

        The account stays locked for the transaction, so concurrent unlinks cannot each remove a different
        link and leave the account without a way to sign in. Login methods are counted before the link is
        looked up, so on a database without row locks the loser of a race for the same link still reads
        ``NOT_FOUND`` instead of ``FINAL_METHOD``.

        Returns:
            ``UNLINKED``, ``NOT_FOUND`` when the user has no such link, or ``FINAL_METHOD`` when
            ``require_remaining`` is set and the link is the account's only login method.
        """
        user = await self.users.find_for_update(user_id)
        if user is None:
            return UnlinkStatus.NOT_FOUND
        login_method_count = await self._count_login_methods(user)
        oauth_account = await self.oauth_accounts.find_owned(oauth_account_id, user_id=user.id, provider=provider)
        if oauth_account is None:
            return UnlinkStatus.NOT_FOUND
        if require_remaining and login_method_count <= 1:
            return UnlinkStatus.FINAL_METHOD
        unlinked = await self.oauth_accounts.unlink(oauth_account)
        return UnlinkStatus.UNLINKED if unlinked else UnlinkStatus.NOT_FOUND

    async def _provision_account(
        self,
        identity: ProviderIdentity,
        *,
        grant: ProviderGrant,
        protected_tokens: ProtectedOAuthSecret | None,
        now: datetime,
    ) -> m.UserOAuthAccount:
        try:
            user = await self.users.provision(
                email=self._provisioning_email(identity),
                name=identity.display_name,
                verified=identity.email_verified,
                now=now,
            )
        except IntegrityError as error:
            if not is_constraint_violation(error):
                raise
            raise AccountLinkError from error
        return await self.oauth_accounts.create_link(
            user.id,
            identity,
            email=user.email,
            grant=grant,
            protected_tokens=protected_tokens,
            now=now,
        )

    @staticmethod
    def _provisioning_email(identity: ProviderIdentity) -> str:
        if identity.email:
            return normalize_identifier(identity.email)
        return f"{identity.provider}-{identity.subject}@oauth.local"

    async def _count_login_methods(self, user: m.User) -> int:
        linked_provider_count = await self.oauth_accounts.count(user_id=user.id)
        passkey_count = await self.passkeys.count(user_id=user.id)
        return linked_provider_count + passkey_count + int(user.hashed_password is not None)


class APIKeyServices(ServiceGroup):
    """Services behind personal API keys and the accounts that own them."""

    api_keys: APIKeyRecordService
    users: UserService
