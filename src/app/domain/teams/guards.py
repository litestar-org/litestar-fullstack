from uuid import UUID

from starlite.connection import ASGIConnection
from starlite.exceptions import NotAuthorizedException
from starlite.handlers.base import BaseRouteHandler

from app.domain.teams.models import TeamRoles

__all__ = ["requires_team_admin", "requires_team_membership", "requires_team_ownership"]


def requires_team_membership(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Verify the connection user is a member of the workspace.

    Args:
        connection (ASGIConnection): _description_
        _ (BaseRouteHandler): _description_

    Raises:
        NotAuthorizedException: _description_
    """
    team_id = connection.path_params["team_id"]
    if connection.user.is_superuser:
        return
    if any(membership.team.id == team_id for membership in connection.user.teams):
        return
    raise NotAuthorizedException(detail="Insufficient permissions to access workspace.")


def requires_team_admin(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Verify the connection user is a workspace admin.

    Args:
        connection (ASGIConnection): _description_
        _ (BaseRouteHandler): _description_

    Raises:
        NotAuthorizedException: _description_
    """
    team_id = connection.path_params["team_id"]
    if connection.user.is_superuser:
        return
    if any(
        membership.team.id == team_id and membership.role == TeamRoles.ADMIN for membership in connection.user.teams
    ):
        return
    raise NotAuthorizedException(detail="Insufficient permissions to access workspace.")


def requires_team_ownership(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Verify that the connection user is the workspace owner.

    Args:
        connection (ASGIConnection): _description_
        _ (BaseRouteHandler): _description_

    Raises:
        NotAuthorizedException: _description_
    """
    team_id = UUID(connection.path_params["team_id"])
    if connection.user.is_superuser:
        return
    if any(membership.team.id == team_id and membership.is_owner for membership in connection.user.teams):
        return
    raise NotAuthorizedException("Insufficient permissions to access workspace.")
