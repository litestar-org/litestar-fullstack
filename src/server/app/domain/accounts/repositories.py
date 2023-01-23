from app.lib import db

from .models import User

__all__ = ["UserRepository"]


class UserRepository(db.SQLAlchemyRepository[User]):
    """User Repository."""
