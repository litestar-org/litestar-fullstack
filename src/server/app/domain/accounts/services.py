from app.lib.service import RepositoryService

from .models import User


class UserService(RepositoryService[User]):
    """User Service."""
