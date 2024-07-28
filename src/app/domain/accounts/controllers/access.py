"""User Account Controllers."""

from __future__ import annotations

from typing import Any

from advanced_alchemy.utils.text import slugify
from litestar import Controller, Request, Response, get, patch, post
from litestar.di import Provide
from litestar.plugins.flash import flash
from litestar_vite.inertia import InertiaRedirect

from app.db.models import User as UserModel  # noqa: TCH001
from app.domain.accounts.dependencies import provide_roles_service, provide_users_service
from app.domain.accounts.guards import requires_active_user
from app.domain.accounts.schemas import AccountLogin, AccountRegister, User
from app.domain.accounts.services import RoleService, UserService


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
    path = "/register"
    include_in_schema = False
    dependencies = {"users_service": Provide(provide_users_service), "roles_service": Provide(provide_roles_service)}
    signature_namespace = {
        "UserService": UserService,
        "RoleService": RoleService,
    }
    exclude_from_auth = True

    @get(component="auth/register", name="register", path="/")
    async def show_signup(
        self,
        request: Request,
    ) -> Response | dict:
        """Show the user login page."""
        if request.session.get("user_id", False):
            flash(request, "Your account is already authenticated.  Welcome back!", category="info")
            return InertiaRedirect(request, request.url_for("dashboard"))
        return {}

    @post(component="auth/register", name="register.add", path="/")
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
        user = await users_service.create(user_data, auto_commit=True)
        request.set_session({"user_id": user.email})
        request.app.emit(event_id="user_created", user_id=user.id)
        flash(request, "Account created successfully.  Welcome!", category="info")
        return InertiaRedirect(request, request.url_for("dashboard"))


class ProfileController(Controller):
    path = "/profile"
    include_in_schema = False
    dependencies = {"users_service": Provide(provide_users_service)}
    signature_namespace = {
        "UserService": UserService,
        "User": User,
    }
    guards = [requires_active_user]

    @get(component="profile/edit", name="profile.show", path="/")
    async def profile(self, current_user: UserModel, users_service: UserService) -> User:
        """User Profile."""
        return users_service.to_schema(current_user, schema_type=User)

    @patch(component="profile/edit", name="profile.edit", path="/")
    async def update_profile(self, current_user: UserModel, users_service: UserService) -> User:
        """User Profile."""
        return users_service.to_schema(current_user, schema_type=User)
