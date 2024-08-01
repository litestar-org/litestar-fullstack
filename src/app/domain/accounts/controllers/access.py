"""User Account Controllers."""

from __future__ import annotations

from typing import Any

from advanced_alchemy.utils.text import slugify
from litestar import Controller, Request, Response, delete, get, patch, post
from litestar.di import Provide
from litestar.plugins.flash import flash
from litestar_vite.inertia import InertiaExternalRedirect, InertiaRedirect, share

from app.config.app import github_oauth2_client, google_oauth2_client
from app.db.models import User as UserModel  # noqa: TCH001
from app.domain.accounts.dependencies import provide_roles_service, provide_users_service
from app.domain.accounts.guards import github_oauth_callback, google_oauth_callback, requires_active_user
from app.domain.accounts.schemas import AccountLogin, AccountRegister, PasswordUpdate, ProfileUpdate, User
from app.domain.accounts.schemas import User as UserSchema
from app.domain.accounts.services import RoleService, UserService
from app.lib.oauth import AccessTokenState
from app.lib.schema import Message


class AccessController(Controller):
    """User login and registration."""

    include_in_schema = False
    dependencies = {"users_service": Provide(provide_users_service)}
    signature_namespace = {
        "UserService": UserService,
    }
    cache = False
    exclude_from_auth = True

    @get(component="auth/login", name="login", path="/login/")
    async def show_login(
        self,
        request: Request,
    ) -> Response | dict:
        """Show the user login page."""
        if request.session.get("user_id", False):
            flash(request, "Your account is already authenticated.", category="info")
            return InertiaRedirect(request, request.url_for("dashboard"))
        return {}

    @post(component="auth/login", name="login.check", path="/login/")
    async def login(
        self,
        request: Request[Any, Any, Any],
        users_service: UserService,
        data: AccountLogin,
    ) -> Response:
        """Authenticate a user."""
        user = await users_service.authenticate(data.username, data.password)
        request.set_session({"user_id": user.email})
        flash(request, "Your account was successfully authenticated.", category="info")
        request.logger.info("Redirecting to %s ", request.url_for("dashboard"))
        return InertiaRedirect(request, request.url_for("dashboard"))

    @post(name="logout", path="/logout/", exclude_from_auth=False)
    async def logout(
        self,
        request: Request,
    ) -> Response:
        """Account Logout"""
        flash(request, "You have been logged out.", category="info")
        request.clear_session()
        return InertiaRedirect(request, request.url_for("login"))


class RegistrationController(Controller):
    include_in_schema = False
    dependencies = {"users_service": Provide(provide_users_service), "roles_service": Provide(provide_roles_service)}
    signature_namespace = {
        "UserService": UserService,
        "RoleService": RoleService,
    }
    exclude_from_auth = True

    @get(component="auth/register", name="register", path="/register/")
    async def show_signup(
        self,
        request: Request,
    ) -> Response | dict:
        """Show the user login page."""
        if request.session.get("user_id", False):
            flash(request, "Your account is already authenticated.  Welcome back!", category="info")
            return InertiaRedirect(request, request.url_for("dashboard"))
        return {}

    @post(component="auth/register", name="register.add", path="/register/")
    async def signup(
        self,
        request: Request,
        users_service: UserService,
        roles_service: RoleService,
        data: AccountRegister,
    ) -> Response:
        """User Signup."""
        user_data = data.to_dict()
        role_obj = await roles_service.get_one_or_none(slug=slugify(users_service.default_role))
        if role_obj is not None:
            user_data.update({"role_id": role_obj.id})
        user = await users_service.create(user_data)
        request.set_session({"user_id": user.email})
        request.app.emit(event_id="user_created", user_id=user.id)
        flash(request, "Account created successfully.  Welcome!", category="info")
        return InertiaRedirect(request, request.url_for("dashboard"))

    @post(name="github.register", path="/register/github/")
    async def github_signup(
        self,
        request: Request,
    ) -> InertiaExternalRedirect:
        """Redirect to the Github Login page."""
        redirect_to = await github_oauth2_client.get_authorization_url(redirect_uri=request.url_for("github.complete"))
        return InertiaExternalRedirect(request, redirect_to=redirect_to)

    @get(
        name="github.complete",
        path="/o/github/complete/",
        dependencies={"access_token_state": Provide(github_oauth_callback)},
        signature_namespace={"AccessTokenState": AccessTokenState},
    )
    async def github_complete(
        self,
        request: Request,
        access_token_state: AccessTokenState,
        users_service: UserService,
    ) -> InertiaRedirect:
        """Redirect to the Github Login page."""
        token, _state = access_token_state
        _id, email = await github_oauth2_client.get_id_email(token=token["access_token"])

        user, created = await users_service.get_or_upsert(
            match_fields=["email"],
            email=email,
            is_verified=True,
            is_active=True,
        )
        request.set_session({"user_id": user.email})
        request.logger.info("github auth request", id=_id, email=email)
        if created:
            request.logger.info("created a new user", id=user.id)
            flash(request, "Welcome to fullstack.  Your account is ready", category="info")
        share(request, "auth", {"isAuthenticated": True, "user": users_service.to_schema(user, schema_type=UserSchema)})
        return InertiaRedirect(request, redirect_to=request.url_for("dashboard"))

    @post(name="google.register", path="/register/google/")
    async def google_signup(
        self,
        request: Request,
    ) -> InertiaExternalRedirect:
        """Redirect to the Github Login page."""
        redirect_to = await google_oauth2_client.get_authorization_url(redirect_uri=request.url_for("google.complete"))
        return InertiaExternalRedirect(request, redirect_to=redirect_to)

    @get(
        name="google.complete",
        path="/o/google/complete/",
        dependencies={"access_token_state": Provide(google_oauth_callback)},
        signature_namespace={"AccessTokenState": AccessTokenState},
    )
    async def google_complete(
        self,
        request: Request,
        access_token_state: AccessTokenState,
        users_service: UserService,
    ) -> InertiaRedirect:
        """Redirect to the Github Login page."""
        token, _state = access_token_state
        _id, email = await google_oauth2_client.get_id_email(token=token["access_token"])

        user, created = await users_service.get_or_upsert(
            match_fields=["email"],
            email=email,
            is_verified=True,
            is_active=True,
        )
        request.set_session({"user_id": user.email})
        request.logger.info("google auth request", id=_id, email=email)
        if created:
            request.logger.info("created a new user", id=user.id)
            flash(request, "Welcome to fullstack.  Your account is ready", category="info")
        share(request, "auth", {"isAuthenticated": True, "user": users_service.to_schema(user, schema_type=UserSchema)})
        return InertiaRedirect(request, redirect_to=request.url_for("dashboard"))


class ProfileController(Controller):
    include_in_schema = False
    dependencies = {"users_service": Provide(provide_users_service)}
    signature_namespace = {
        "UserService": UserService,
        "User": User,
    }
    guards = [requires_active_user]

    @get(component="profile/edit", name="profile.show", path="/profile/")
    async def profile(self, current_user: UserModel, users_service: UserService) -> User:
        """User Profile."""
        return users_service.to_schema(current_user, schema_type=User)

    @patch(component="profile/edit", name="profile.update", path="/profile/")
    async def update_profile(self, current_user: UserModel, data: ProfileUpdate, users_service: UserService) -> User:
        """User Profile."""
        db_obj = await users_service.update(data, item_id=current_user.id)
        return users_service.to_schema(db_obj, schema_type=User)

    @patch(component="profile/edit", name="password.update", path="/profile/password-update/")
    async def update_password(
        self,
        current_user: UserModel,
        data: PasswordUpdate,
        users_service: UserService,
    ) -> Message:
        """Update user password."""
        await users_service.update_password(data.to_dict(), db_obj=current_user)
        return Message(message="Your password was successfully modified.")

    @delete(name="account.remove", path="/profile/", status_code=303)
    async def remove_account(
        self,
        request: Request,
        current_user: UserModel,
        users_service: UserService,
    ) -> InertiaRedirect:
        """Remove your account."""
        request.session.clear()
        _ = await users_service.delete(current_user.id)
        flash(request, "Your account has been removed from the system.", category="info")
        return InertiaRedirect(request, request.url_for("landing"))
