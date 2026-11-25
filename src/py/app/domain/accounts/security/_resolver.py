"""Zero-I/O authorization snapshot resolver and domain authorization predicates."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from advanced_alchemy.utils.text import slugify
from litestar import Router
from litestar.exceptions import PermissionDeniedException
from litestar_security.authentication import InvalidCredentials, VerificationUnavailable
from litestar_security.context import AuthorizationSnapshot, Principal, SecurityContext
from litestar_security.guards import (
    AuthorizationDecision,
    AuthorizationPredicate,
    requires_any_of,
    requires_role,
    requires_tenant_role,
)
from sqlalchemy.exc import SQLAlchemyError

from app.lib.constants import DEFAULT_ACCESS_ROLE, SUPERUSER_ACCESS_ROLE

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection
    from litestar.handlers import BaseRouteHandler

    from app.db import models as m

APPLICATION_ACCESS_REQUIRED = "application_access_required"
TEAM_ROLE_EXPANSION: dict[str, frozenset[str]] = {
    "MEMBER": frozenset({"member"}),
    "ADMIN": frozenset({"member", "admin"}),
}

_APPLICATION_ACCESS_ROLES = frozenset({slugify(DEFAULT_ACCESS_ROLE), "superuser"})
_SIGN_OUT_ROUTE = "local.session.logout"

__all__ = (
    "APPLICATION_ACCESS_REQUIRED",
    "TEAM_ROLE_EXPANSION",
    "AppAuthorizationResolver",
    "ApplicationAccessRouter",
    "SelfSubjectPredicate",
    "require_application_access",
    "requires_self_or_superuser",
    "requires_team_role",
)


class AppAuthorizationResolver:
    """Zero-I/O ``AuthorizationResolver`` expanding global and additive hierarchical team roles."""

    __slots__ = ()

    async def resolve(  # NOSONAR - the AuthorizationResolver protocol awaits this method
        self,
        principal: Principal[m.User],
    ) -> AuthorizationSnapshot | InvalidCredentials | VerificationUnavailable:
        """Compute an immutable ``AuthorizationSnapshot`` purely from eager-loaded ``User`` attributes.

        Returns:
            Computed ``AuthorizationSnapshot``, ``InvalidCredentials`` if user is missing, or ``VerificationUnavailable``.
        """
        if not principal.is_authenticated:
            return AuthorizationSnapshot()
        user = principal.user
        if user is None:
            return InvalidCredentials()
        try:
            roles: set[str] = {
                assigned.role_slug.lower() for assigned in user.roles if getattr(assigned, "role_slug", None)
            }
            if user.is_superuser or SUPERUSER_ACCESS_ROLE.lower() in roles:
                roles.add("superuser")

            tenant_roles: dict[str, frozenset[str]] = {}
            for membership in user.teams:
                raw_role = membership.role
                role_key = str(getattr(raw_role, "value", raw_role)).upper()
                expanded = set(TEAM_ROLE_EXPANSION.get(role_key, frozenset({"member"})))
                if membership.is_owner:
                    expanded.update({"admin", "owner"})
                tenant_roles[str(membership.team_id)] = frozenset(expanded)
        except SQLAlchemyError:
            return VerificationUnavailable()

        return AuthorizationSnapshot(
            roles=frozenset(roles),
            tenant_roles=tenant_roles,
            tenant_ids=frozenset(tenant_roles.keys()),
        )


class SelfSubjectPredicate(AuthorizationPredicate):
    """Authorization predicate granting access when a path parameter matches the authenticated principal ID."""

    __slots__ = ("parameter",)

    def __init__(self, parameter: str = "user_id") -> None:
        """Initialize the predicate targeting the named path parameter."""
        self.parameter = parameter

    def decide(self, connection: ASGIConnection[Any, Any, Any, Any]) -> AuthorizationDecision:
        """Evaluate whether the authenticated principal matches the path parameter value.

        Returns:
            Grant decision when IDs match, otherwise an unauthenticated or forbidden denial.
        """
        principal: object = cast("dict[str, Any]", connection.scope).get("user")
        if not isinstance(principal, Principal) or not principal.is_authenticated or principal.id is None:
            return AuthorizationDecision(
                granted=False,
                code="authentication_required",
                authentication_required=True,
            )
        target = connection.path_params.get(self.parameter)
        if target is not None and str(target) == str(principal.id):
            return AuthorizationDecision(granted=True)
        return AuthorizationDecision(granted=False, code="forbidden")


def require_application_access(connection: ASGIConnection[Any, Any, Any, Any], route_handler: BaseRouteHandler) -> None:
    """Deny signed-in principals that hold neither the default access role nor ``superuser``.

    Anonymous connections pass, because each route's authentication policy decides whether they are
    admitted. Signing out stays available so an account without access can end its session.

    Raises:
        PermissionDeniedException: If the principal is signed in without the default access role. The client
            sees a problem-details body whose top-level ``code`` member is ``APPLICATION_ACCESS_REQUIRED``.
    """
    security_context: object = cast("dict[str, Any]", connection.scope).get("auth")
    if not isinstance(security_context, SecurityContext) or not security_context.evidence:
        return
    if route_handler.name == _SIGN_OUT_ROUTE or security_context.authorization.roles & _APPLICATION_ACCESS_ROLES:
        return
    raise PermissionDeniedException(
        detail="Your account does not have access to this application.",
        extra={"code": APPLICATION_ACCESS_REQUIRED},
    )


class ApplicationAccessRouter(Router):
    """Router placing the application's own controllers behind ``require_application_access``.

    Route discovery wraps every domain controller in this router, which keeps the guard off routes the
    security configuration excludes, such as static files.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the router with the application-access guard ahead of any guards passed in."""
        guards = [require_application_access, *kwargs.pop("guards", ())]
        super().__init__(*args, guards=guards, **kwargs)  # pyright: ignore[reportUnknownMemberType]


def requires_team_role(*roles: str) -> AuthorizationPredicate:
    """Require either global ``superuser`` role or one of the specified roles on path ``team_id``.

    Returns:
        Composite authorization predicate enforcing the team role requirement.
    """
    return requires_any_of(
        requires_role("superuser"),
        requires_tenant_role(tenant_parameter="team_id", roles=frozenset(roles)),
    )


requires_self_or_superuser: AuthorizationPredicate = requires_any_of(
    requires_role("superuser"),
    SelfSubjectPredicate(),
)
