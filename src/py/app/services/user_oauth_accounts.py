from __future__ import annotations

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from app.db import models as m


class UserOAuthAccountService(SQLAlchemyAsyncRepositoryService[m.UserOauthAccount]):
    """Handles database operations for user OAuth external authorization."""

    class Repo(SQLAlchemyAsyncRepository[m.UserOauthAccount]):
        """User SQLAlchemy Repository."""

        model_type = m.UserOauthAccount

    repository_type = Repo
