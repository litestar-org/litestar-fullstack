from pydantic import UUID4
from starlite import BaseRouteHandler, NotAuthorizedException, Request

from app import services

__all__ = [
    "requires_active_user",
    "requires_superuser",
    "requires_team_membership",
    "requires_team_ownership",
    "requires_team_admin",
]


def requires_active_user(request: Request, _: BaseRouteHandler) -> None:
    if not services.user.is_active(request.user):
        raise NotAuthorizedException("Inactive account")


def requires_superuser(request: Request, _: BaseRouteHandler) -> None:

    if services.user.is_superuser(request.user):
        return None
    raise NotAuthorizedException("Inactive account")


def requires_team_membership(request: Request, _: BaseRouteHandler) -> None:
    team_id = request.path_params["team_id"]
    if services.user.is_superuser(request.user):
        return None
    if services.user.is_team_member(request.user, team_id):
        return None
    raise NotAuthorizedException("Insufficient permissions to access team.")


def requires_team_admin(request: Request, _: BaseRouteHandler) -> None:
    team_id = request.path_params["team_id"]
    if services.user.is_superuser(request.user):
        return None
    if not services.user.is_team_admin(request.user, team_id):
        raise NotAuthorizedException("Insufficient permissions to access team.")


def requires_team_ownership(request: Request, _: BaseRouteHandler) -> None:
    team_id = UUID4(request.path_params["team_id"])
    if services.user.is_superuser(request.user) or services.user.is_team_owner(request.user, team_id):
        return None
    raise NotAuthorizedException("Insufficient permissions to access team.")
