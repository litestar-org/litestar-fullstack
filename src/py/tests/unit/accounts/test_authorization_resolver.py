"""Unit tests for AppAuthorizationResolver and custom authorization predicates."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest
from litestar_security.authentication import InvalidCredentials
from litestar_security.context import AuthorizationSnapshot, Principal

from app.db import models as m
from app.domain.accounts.security.resolver import (
    TEAM_ROLE_EXPANSION,
    AppAuthorizationResolver,
    SelfSubjectPredicate,
    requires_self_or_superuser,
    requires_team_role,
)

pytestmark = pytest.mark.anyio


def _fake_connection(
    *,
    principal: Principal[Any] | None = None,
    snapshot: AuthorizationSnapshot | None = None,
    path_params: dict[str, Any] | None = None,
) -> Any:
    scope: dict[str, Any] = {}
    if principal is not None:
        scope["user"] = principal
    if snapshot is not None:
        scope["auth"] = SimpleNamespace(authorization=snapshot, principal=principal)
    return SimpleNamespace(scope=scope, path_params=path_params or {})


async def test_resolver_anonymous_and_missing_user() -> None:
    resolver = AppAuthorizationResolver()
    anon = Principal[m.User](id=None)
    assert await resolver.resolve(anon) == AuthorizationSnapshot()

    missing_user = Principal[m.User](id=str(uuid4()), user=None)
    assert isinstance(await resolver.resolve(missing_user), InvalidCredentials)


async def test_resolver_expands_global_and_hierarchical_team_roles() -> None:
    resolver = AppAuthorizationResolver()
    team_member_id = uuid4()
    team_admin_id = uuid4()
    team_owner_id = uuid4()

    user = SimpleNamespace(
        id=uuid4(),
        is_superuser=False,
        roles=[SimpleNamespace(role_slug="User")],
        teams=[
            SimpleNamespace(team_id=team_member_id, role=m.TeamRoles.MEMBER, is_owner=False),
            SimpleNamespace(team_id=team_admin_id, role=m.TeamRoles.ADMIN, is_owner=False),
            SimpleNamespace(team_id=team_owner_id, role=m.TeamRoles.MEMBER, is_owner=True),
        ],
    )
    principal = Principal(id=str(user.id), user=cast("m.User", user))
    snapshot = await resolver.resolve(principal)
    assert isinstance(snapshot, AuthorizationSnapshot)
    assert snapshot.roles == frozenset({"user"})
    assert snapshot.tenant_roles[str(team_member_id)] == TEAM_ROLE_EXPANSION["MEMBER"]
    assert snapshot.tenant_roles[str(team_admin_id)] == TEAM_ROLE_EXPANSION["ADMIN"]
    assert snapshot.tenant_roles[str(team_owner_id)] == frozenset({"member", "admin", "owner"})
    assert snapshot.tenant_ids == frozenset({str(team_member_id), str(team_admin_id), str(team_owner_id)})


async def test_resolver_grants_superuser_from_flag_or_role() -> None:
    resolver = AppAuthorizationResolver()

    flag_user = SimpleNamespace(id=uuid4(), is_superuser=True, roles=[], teams=[])
    flag_snap = await resolver.resolve(Principal(id=str(flag_user.id), user=cast("m.User", flag_user)))
    assert isinstance(flag_snap, AuthorizationSnapshot)
    assert "superuser" in flag_snap.roles

    role_user = SimpleNamespace(
        id=uuid4(),
        is_superuser=False,
        roles=[SimpleNamespace(role_slug="Superuser")],
        teams=[],
    )
    role_snap = await resolver.resolve(Principal(id=str(role_user.id), user=cast("m.User", role_user)))
    assert isinstance(role_snap, AuthorizationSnapshot)
    assert "superuser" in role_snap.roles


def test_self_subject_and_team_role_predicates() -> None:
    predicate = SelfSubjectPredicate("user_id")
    uid = str(uuid4())
    other_uid = str(uuid4())

    anon_decision = predicate.decide(_fake_connection(path_params={"user_id": uid}))
    assert anon_decision.granted is False
    assert anon_decision.authentication_required is True

    principal = Principal[object](id=uid)
    assert predicate.decide(_fake_connection(principal=principal, path_params={"user_id": uid})).granted is True
    assert predicate.decide(_fake_connection(principal=principal, path_params={"user_id": other_uid})).granted is False
    assert requires_self_or_superuser is not None
    assert requires_team_role("admin", "owner") is not None
