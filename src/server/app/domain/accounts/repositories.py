from app.lib import db

from .models import User


class UserRepository(db.SQLAlchemyRepository[User]):
    """User Repository."""
