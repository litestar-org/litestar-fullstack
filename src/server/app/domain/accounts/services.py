from app.lib.service import RepositoryService

from .models import User

__all__ = ["UserService"]


class UserService(RepositoryService[User]):
    """User Service."""
