"""User account database service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy.extensions.litestar import service
from litestar.exceptions import ClientException, PermissionDeniedException
from litestar_security.accounts import (
    Argon2PasswordHasher,
    LocalAccountState,
    LoginMethod,
    PasswordCredentialState,
    PasswordPolicy,
    PasswordPolicyViolation,
    normalize_identifier,
)
from sqlalchemy import select, update
from sqlalchemy.orm import undefer_group

from app.db import models as m
from app.domain.accounts.services._role import RoleService
from app.domain.accounts.services._session import UserSessionService
from app.domain.accounts.services._statements import ACCOUNT_STATE_LOAD, affected_rows

if TYPE_CHECKING:
    from advanced_alchemy.service import ModelDictT
    from sqlalchemy import ColumnElement

_COMMON_PASSWORDS = frozenset({"administrator", "password1234", "password12345"})
PASSWORD_POLICY = PasswordPolicy(
    minimum_length=12,
    maximum_length=128,
    compromised=lambda password: password.casefold() in _COMMON_PASSWORDS,
)
"""The one rule set every new password must satisfy, wherever it is chosen.

A password is 12 to 128 characters long and is not on the common-password list, whatever its letter case.
A caller that knows the account also passes its email address, which the password may not repeat. The
security configuration hands the policy to ``LocalAuth`` for sign-up, password reset, and its own password
change; ``UserService.hash_password`` applies it everywhere the application sets a password.
"""

_PASSWORD_HASHER = Argon2PasswordHasher()
_PASSWORD_VIOLATION_MESSAGES = {
    PasswordPolicyViolation.TOO_SHORT: f"Password must be at least {PASSWORD_POLICY.minimum_length} characters long.",
    PasswordPolicyViolation.TOO_LONG: f"Password must not exceed {PASSWORD_POLICY.maximum_length} characters.",
    PasswordPolicyViolation.TOO_MANY_BYTES: f"Password must not exceed {PASSWORD_POLICY.maximum_bytes} bytes.",
    PasswordPolicyViolation.INVALID_TEXT: "Password must be valid text.",
    PasswordPolicyViolation.MATCHES_IDENTIFIER: "Password must not be the same as the email address.",
    PasswordPolicyViolation.COMPROMISED: "Password is too common. Choose one that is harder to guess.",
}


class UserService(service.SQLAlchemyAsyncRepositoryService[m.User]):
    """Handles database operations for user accounts using Argon2 password hashing."""

    match_fields = ["email"]

    async def to_model_on_create(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        """Normalize the email address, hash a plaintext password, and attach an initial role before creation.

        Returns:
            Normalized user payload or model instance ready for persistence.
        """
        return await self._populate_model(data)

    async def to_model_on_update(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        """Normalize the email address when updating a user record.

        An update never replaces a password: ``set_password`` does, so the security epoch advances and the
        user's sessions end with it.

        Returns:
            Normalized user payload or model instance ready for update.
        """
        return self._normalize_email(service.schema_dump(data))

    async def to_model_on_upsert(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        """Normalize the email address and hash a plaintext password when upserting a user record.

        Returns:
            Normalized user payload or model instance ready for upsert.
        """
        return await self._populate_model(data)

    @staticmethod
    def to_user_id(account_id: str | None) -> UUID | None:
        """Translate the security library's account identifier into the user's primary key.

        This is the inverse of the ``account_id=str(user.id)`` that ``to_account_state`` hands the library.

        Returns:
            The user identifier, or ``None`` when ``account_id`` is blank or does not name a user.
        """
        if not account_id:
            return None
        try:
            return UUID(account_id)
        except ValueError:
            return None

    @staticmethod
    def to_account_state(user: m.User) -> LocalAccountState[m.User]:
        """Translate a user loaded by ``find_for_authorization`` into the security library's account projection.

        Returns:
            Account state carrying the identifier, activity flags, security epoch, and the user itself.
        """
        return LocalAccountState(
            account_id=str(user.id),
            normalized_identifier=user.email,
            display_name=user.name,
            active=user.is_active,
            verified=user.is_verified,
            security_epoch=user.security_epoch,
            user=user,
        )

    @staticmethod
    def to_password_state(user: m.User) -> PasswordCredentialState | None:
        """Translate a user loaded by ``find_with_password`` into its password credential snapshot.

        Returns:
            The password hash paired with the account state it was read with, or ``None`` without a password.
        """
        if user.hashed_password is None:
            return None
        return PasswordCredentialState(
            password_hash=user.hashed_password,
            security_epoch=user.security_epoch,
            active=user.is_active,
            verified=user.is_verified,
        )

    @staticmethod
    def to_login_method(user: m.User) -> LoginMethod:
        """Describe the user's password as a ``LoginMethod``.

        Returns:
            Password login method dated from the account's creation.
        """
        return LoginMethod(method_id="password", kind="password", created_at=user.created_at)

    async def find_for_authorization(self, criterion: ColumnElement[bool]) -> m.User | None:
        """Load the user matching ``criterion`` with the roles, teams, and MFA factors authorization reads.

        Returns:
            The user ready for ``to_account_state``, or ``None`` when no user matches.
        """
        return await self.get_one_or_none(criterion, load=ACCOUNT_STATE_LOAD)

    async def find_with_password(self, user_id: UUID) -> m.User | None:
        """Load a user together with its deferred password hash.

        Returns:
            The user, or ``None`` when the account does not exist.
        """
        return await self.get_one_or_none(m.User.id == user_id, load=[undefer_group("security_sensitive")])

    async def find_for_update(self, user_id: UUID) -> m.User | None:
        """Load a user with its password hash and keep its row locked until the transaction ends.

        Changes that depend on the account's complete set of login methods or recovery codes take this lock
        first, so concurrent changes to one account run one at a time.

        Returns:
            The locked user, or ``None`` when the account does not exist.
        """
        return await self.get_one_or_none(
            m.User.id == user_id,
            load=[undefer_group("security_sensitive")],
            with_for_update=True,
        )

    async def find_by_email(self, email: str) -> m.User | None:
        """Load the account an email address identifies, however the address is capitalized or padded.

        Returns:
            The user, or ``None`` when no account has that address.
        """
        return await self.get_one_or_none(email=normalize_identifier(email))

    async def get_by_email(self, email: str) -> m.User:
        """Load the account an email address identifies, however the address is capitalized or padded.

        A missing account surfaces as the ``NotFoundError`` raised by ``get_one``.

        Returns:
            The user holding that address.
        """
        return await self.get_one(email=normalize_identifier(email))

    async def get_security_epoch(self, user_id: UUID) -> int | None:
        """Read an account's security epoch without loading the account.

        Returns:
            The current epoch, or ``None`` when the account does not exist.
        """
        statement = select(m.User.security_epoch).where(m.User.id == user_id)
        security_epoch: int | None = await self.repository.session.scalar(statement)
        return security_epoch

    async def provision(
        self,
        *,
        email: str,
        name: str | None,
        verified: bool,
        now: datetime,
        hashed_password: str | None = None,
        is_superuser: bool = False,
    ) -> m.User:
        """Create an active account holding the default access role inside the caller's transaction.

        The default access role is created first when the database does not have it yet, so no account is
        ever provisioned without it.

        Args:
            email: Email address identifying the account, stored normalized.
            name: Display name, when known.
            verified: Whether the email address is already confirmed.
            now: Timestamp recorded for verification and the role assignment.
            hashed_password: Argon2 hash for password accounts; ``None`` for accounts that sign in another way.
            is_superuser: Whether the account bypasses role checks.

        Returns:
            The flushed user record.
        """
        user = await self.create(
            m.User(
                email=normalize_identifier(email),
                name=name,
                hashed_password=hashed_password,
                is_active=True,
                is_verified=verified,
                is_superuser=is_superuser,
                verified_at=now.date() if verified else None,
                security_epoch=1,
            )
        )
        db_session = self.repository.session
        default_access_role = await RoleService(session=db_session).ensure_default_access_role()
        db_session.add(m.UserRole(user_id=user.id, role_id=default_access_role.id, assigned_at=now))
        await db_session.flush()
        return user

    async def reload_for_authorization(self, user: m.User) -> m.User:
        """Refresh a user changed in this transaction together with everything authorization reads.

        Returns:
            The same user, reflecting the roles, teams, and MFA factors now stored for it.
        """
        return await self.get(user.id, load=ACCOUNT_STATE_LOAD, execution_options={"populate_existing": True})

    async def swap_password_hash(self, user_id: UUID, *, expected_hash: str, password_hash: str) -> bool:
        """Replace the password hash only while the stored hash still equals ``expected_hash``.

        Returns:
            ``True`` when the hash was replaced, ``False`` when it had already changed.
        """
        statement = (
            update(m.User)
            .where(m.User.id == user_id, m.User.hashed_password == expected_hash)
            .values(hashed_password=password_hash)
        )
        return await affected_rows(self.repository.session, statement) == 1

    async def replace_password_hash_and_bump_epoch(
        self,
        user_id: UUID,
        password_hash: str,
        *,
        expected_epoch: int,
        reset_at: datetime | None = None,
    ) -> bool:
        """Replace the password hash and advance the security epoch only while it equals ``expected_epoch``.

        Args:
            user_id: Account whose password is replaced.
            password_hash: Encoded replacement hash.
            expected_epoch: Epoch the caller read; any other stored epoch leaves the account untouched.
            reset_at: Timestamp to record when the replacement completes a password reset.

        Returns:
            ``True`` when the password and epoch changed, ``False`` when the epoch had already moved on.
        """
        statement = (
            update(m.User)
            .where(m.User.id == user_id, m.User.security_epoch == expected_epoch)
            .values(hashed_password=password_hash, security_epoch=expected_epoch + 1)
        )
        if reset_at is not None:
            statement = statement.values(password_reset_at=reset_at)
        return await affected_rows(self.repository.session, statement) == 1

    @staticmethod
    async def hash_password(password: str, *, email: str | None) -> str:
        """Hash a plaintext password that satisfies the application's password policy.

        Every password the application itself sets passes through here, so ``PASSWORD_POLICY`` is the only
        rule a new password meets.

        Args:
            password: Plaintext password chosen for the account.
            email: Email address of the account, which the password must not repeat, when it is known.

        Returns:
            Encoded Argon2 hash.

        Raises:
            ClientException: If the policy rejects the password. The detail names every violated rule.
        """
        violations = PASSWORD_POLICY.check(password, normalized_identifier=email).violations
        if violations:
            raise ClientException(
                detail=" ".join(
                    message for violation, message in _PASSWORD_VIOLATION_MESSAGES.items() if violation in violations
                )
            )
        return await _PASSWORD_HASHER.hash(password)

    async def set_password(self, user: m.User, password: str) -> None:
        """Give a user a new password inside the caller's transaction, signing the account out everywhere.

        Advancing the security epoch and revoking every session ends whatever the previous password had
        opened. ``user`` reflects its new credentials when this returns.

        Raises:
            ClientException: If ``hash_password`` rejects the password, or the account's credentials changed
                after ``user`` was loaded.
        """
        password_hash = await self.hash_password(password, email=user.email)
        password_replaced = await self.replace_password_hash_and_bump_epoch(
            user.id,
            password_hash,
            expected_epoch=user.security_epoch,
        )
        if not password_replaced:
            raise ClientException(detail="The account's credentials changed. Try again.", status_code=409)
        db_session = self.repository.session
        await UserSessionService(session=db_session).revoke_all_for_user(user.id, now=datetime.now(UTC))
        await db_session.refresh(user, ["hashed_password", "has_password", "security_epoch"])

    async def update_password(self, user: m.User, *, current_password: str, new_password: str) -> None:
        """Replace the user's password after verifying the current one, signing the account out everywhere.

        A rejected new password, or credentials that changed while this request was verifying them, surface
        as the ``ClientException`` raised by ``set_password``.

        Args:
            user: Account changing its password.
            current_password: Plaintext password the account holds now.
            new_password: Plaintext replacement password.

        Raises:
            PermissionDeniedException: If current password verification fails or the account is inactive.
        """
        account = await self.find_with_password(user.id)
        if account is None or account.hashed_password is None:
            msg = "User not found or password invalid."
            raise PermissionDeniedException(detail=msg)
        outcome = await _PASSWORD_HASHER.verify(account.hashed_password, current_password)
        if not outcome.verified:
            msg = "User not found or password invalid."
            raise PermissionDeniedException(detail=msg)
        if not account.is_active:
            msg = "User account is not active"
            raise PermissionDeniedException(detail=msg)

        await self.set_password(account, new_password)
        await self.repository.session.commit()

    async def _populate_model(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        dumped: ModelDictT[m.User] = self._normalize_email(service.schema_dump(data))
        dumped = await self._populate_with_hashed_password(dumped)
        return await self._populate_with_role(dumped)

    @staticmethod
    def _normalize_email(data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        if service.is_dict_with_field(data, "email") and isinstance(data["email"], str):
            data["email"] = normalize_identifier(data["email"])
        return data

    async def _populate_with_hashed_password(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        if service.is_dict(data) and (password := data.pop("password", None)) is not None:
            data["hashed_password"] = await self.hash_password(str(password), email=data.get("email"))
        return data

    async def _populate_with_role(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        if service.is_dict(data) and (role_id := data.pop("role_id", None)) is not None:
            user = await self.to_model(data)
            user.roles.append(m.UserRole(role_id=role_id, assigned_at=datetime.now(UTC)))
            return user
        return data
