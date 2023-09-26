from uuid import UUID

from litestar.connection import ASGIConnection
from litestar.exceptions import PermissionDeniedException
from litestar.handlers.base import BaseRouteHandler

from app.domain.teams.models import TeamRoles

__all__ = ["requires_team_admin", "requires_team_membership", "requires_team_ownership"]


def requires_team_membership(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Verify the connection user is a member of the team.

    Args:
        connection (ASGIConnection): _description_
        _ (BaseRouteHandler): _description_

    Raises:
        PermissionDeniedException: _description_
    """
    team_id = connection.path_params["team_id"]
    if connection.user.is_superuser:
        return
    if any(membership.team.id == team_id for membership in connection.user.teams):
        return
    raise PermissionDeniedException(detail="Insufficient permissions to access workspace.")


def requires_team_admin(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Verify the connection user is a team admin.

    Args:
        connection (ASGIConnection): _description_
        _ (BaseRouteHandler): _description_

    Raises:
        PermissionDeniedException: _description_
    """
    team_id = connection.path_params["team_id"]
    if connection.user.is_superuser:
        return
    if any(
        membership.team.id == team_id and membership.role == TeamRoles.ADMIN for membership in connection.user.teams
    ):
        return
    raise PermissionDeniedException(detail="Insufficient permissions to access team.")


def requires_team_ownership(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Verify that the connection user is the team owner.

    Args:
        connection (ASGIConnection): _description_
        _ (BaseRouteHandler): _description_

    Raises:
        PermissionDeniedException: _description_
    """
    team_id = UUID(connection.path_params["team_id"])
    if connection.user.is_superuser:
        return
    if any(membership.team.id == team_id and membership.is_owner for membership in connection.user.teams):
        return
    msg = "Insufficient permissions to access team."
    raise PermissionDeniedException(msg)
