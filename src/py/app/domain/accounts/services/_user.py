"""User account database service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy.extensions.litestar import service
from litestar.exceptions import ClientException, PermissionDeniedException
from litestar_security.accounts import Argon2PasswordHasher, LocalAccountState, LoginMethod, PasswordCredentialState
from sqlalchemy import select, update
from sqlalchemy.orm import undefer_group

from app.db import models as m
from app.domain.accounts.services._role import RoleService
from app.domain.accounts.services._session import UserSessionService
from app.domain.accounts.services._statements import ACCOUNT_STATE_LOAD, affected_rows
from app.lib import constants
from app.lib.validation import PasswordValidationError, validate_password_strength

if TYPE_CHECKING:
    from advanced_alchemy.service import ModelDictT
    from sqlalchemy import ColumnElement

_PASSWORD_HASHER = Argon2PasswordHasher()


class UserService(service.SQLAlchemyAsyncRepositoryService[m.User]):
    """Handles database operations for user accounts using Argon2 password hashing."""

    default_role = constants.DEFAULT_ACCESS_ROLE
    match_fields = ["email"]

    async def to_model_on_create(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        """Hash plaintext passwords and attach initial role assignments before creation.

        Returns:
            Normalized user payload or model instance ready for persistence.
        """
        return await self._populate_model(data)

    async def to_model_on_update(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        """Hash plaintext passwords when updating a user record.

        Returns:
            Normalized user payload or model instance ready for update.
        """
        return await self._populate_model(data)

    async def to_model_on_upsert(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        """Hash plaintext passwords when upserting a user record.

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
            email: Normalized email address identifying the account.
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
                email=email,
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
        roles = RoleService(session=db_session)
        default_role = await roles.get_one_or_none(name=self.default_role) or await roles.create(
            {"name": self.default_role, "description": constants.DEFAULT_ACCESS_ROLE_DESCRIPTION}
        )
        db_session.add(m.UserRole(user_id=user.id, role_id=default_role.id, assigned_at=now))
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
    async def hash_password(password: str) -> str:
        """Hash a plaintext password with the application's Argon2 parameters.

        Returns:
            Encoded Argon2 hash.
        """
        return await _PASSWORD_HASHER.hash(password)

    async def authenticate(self, username: str, password: str) -> m.User:
        """Verify email and password against the stored Argon2 hash.

        Args:
            username: User email address.
            password: Candidate plaintext password.

        Returns:
            The authenticated active user record.

        Raises:
            PermissionDeniedException: If credentials are invalid or the account is inactive.
        """
        user = await self.get_one_or_none(email=username, load=[undefer_group("security_sensitive")])
        if user is None or user.hashed_password is None:
            msg = "User not found or password invalid"
            raise PermissionDeniedException(detail=msg)
        outcome = await _PASSWORD_HASHER.verify(user.hashed_password, password)
        if not outcome.verified:
            msg = "User not found or password invalid"
            raise PermissionDeniedException(detail=msg)
        if not user.is_active:
            msg = "User account is inactive"
            raise PermissionDeniedException(detail=msg)
        return user

    async def verify_email(self, user_id: UUID, email: str) -> m.User:
        """Mark a user's email address as verified.

        Args:
            user_id: Target user UUID.
            email: Verified email address expected to match the account.

        Returns:
            The updated user record.

        Raises:
            ClientException: If the user does not exist or the email does not match.
        """
        user = await self.get_one_or_none(id=user_id)
        if user is None:
            raise ClientException(detail="User not found", status_code=404)
        if user.email != email:
            raise ClientException(detail="Email address does not match user account", status_code=400)
        user.is_verified = True
        user.verified_at = datetime.now(UTC).date()
        return await self.update(data=user)

    async def update_password(self, user: m.User, *, current_password: str, new_password: str) -> None:
        """Replace the user's password after verifying the current one, signing the account out everywhere.

        Args:
            user: Account changing its password.
            current_password: Plaintext password the account holds now.
            new_password: Plaintext replacement password.

        Raises:
            ClientException: If the new password fails strength validation, or the account's credentials
                changed while this request was verifying them.
            PermissionDeniedException: If current password verification fails or the account is inactive.
        """
        try:
            validate_password_strength(new_password)
        except PasswordValidationError as error:
            raise ClientException(detail=str(error), status_code=400) from error

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

        password_hash = await _PASSWORD_HASHER.hash(new_password)
        password_replaced = await self.replace_password_hash_and_bump_epoch(
            account.id,
            password_hash,
            expected_epoch=account.security_epoch,
        )
        if not password_replaced:
            raise ClientException(detail="Your credentials changed. Sign in again and retry.", status_code=409)
        db_session = self.repository.session
        await UserSessionService(session=db_session).revoke_all_for_user(account.id, now=datetime.now(UTC))
        await db_session.commit()

    @staticmethod
    async def has_role_id(user: m.User, role_id: UUID) -> bool:
        """Return whether the user holds the role identified by ``role_id``."""
        return any(assigned.role_id == role_id for assigned in user.roles)

    @staticmethod
    async def has_role(user: m.User, role_name: str) -> bool:
        """Return whether the user holds the named role."""
        return any(assigned.role_name == role_name for assigned in user.roles)

    @staticmethod
    def is_superuser(user: m.User) -> bool:
        """Return whether the user is a superuser via flag or role assignment."""
        return bool(
            user.is_superuser or any(assigned.role_name == constants.SUPERUSER_ACCESS_ROLE for assigned in user.roles),
        )

    async def _populate_model(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        dumped: ModelDictT[m.User] = service.schema_dump(data)
        dumped = await self._populate_with_hashed_password(dumped)
        return await self._populate_with_role(dumped)

    async def _populate_with_hashed_password(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        if service.is_dict(data) and (password := data.pop("password", None)) is not None:
            data["hashed_password"] = await _PASSWORD_HASHER.hash(str(password))
        return data

    async def _populate_with_role(self, data: ModelDictT[m.User]) -> ModelDictT[m.User]:
        if service.is_dict(data) and (role_id := data.pop("role_id", None)) is not None:
            user = await self.to_model(data)
            user.roles.append(m.UserRole(role_id=role_id, assigned_at=datetime.now(UTC)))
            return user
        return data
