"""Zero-I/O authorization snapshot resolver and domain authorization predicates."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from litestar_security.authentication import InvalidCredentials, VerificationUnavailable
from litestar_security.context import AuthorizationSnapshot, Principal
from litestar_security.guards import (
    AuthorizationDecision,
    AuthorizationPredicate,
    requires_any_of,
    requires_role,
    requires_tenant_role,
)
from sqlalchemy.exc import SQLAlchemyError

from app.lib.constants import SUPERUSER_ACCESS_ROLE

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection

    from app.db import models as m

TEAM_ROLE_EXPANSION: dict[str, frozenset[str]] = {
    "MEMBER": frozenset({"member"}),
    "ADMIN": frozenset({"member", "admin"}),
}

__all__ = (
    "TEAM_ROLE_EXPANSION",
    "AppAuthorizationResolver",
    "SelfSubjectPredicate",
    "requires_self_or_superuser",
    "requires_team_role",
)


class AppAuthorizationResolver:
    """Zero-I/O ``AuthorizationResolver`` expanding global and additive hierarchical team roles."""

    __slots__ = ()

    async def resolve(
        self,
        principal: Principal[m.User],
    ) -> AuthorizationSnapshot | InvalidCredentials | VerificationUnavailable:
        """Compute an immutable ``AuthorizationSnapshot`` purely from eager-loaded ``User`` attributes."""
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
        """Evaluate whether the authenticated principal matches the path parameter value."""
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


def requires_team_role(*roles: str) -> AuthorizationPredicate:
    """Require either global ``superuser`` role or one of the specified roles on path ``team_id``."""
    return requires_any_of(
        requires_role("superuser"),
        requires_tenant_role(tenant_parameter="team_id", roles=frozenset(roles)),
    )


requires_self_or_superuser: AuthorizationPredicate = requires_any_of(
    requires_role("superuser"),
    SelfSubjectPredicate(),
)
