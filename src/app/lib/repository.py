from __future__ import annotations

import random
import string
from typing import TYPE_CHECKING, Any

from litestar.contrib.repository.handlers import on_app_init as _on_app_init
from litestar.contrib.sqlalchemy.repository import ModelT, SQLAlchemyAsyncRepository

from app.utils import slugify

if TYPE_CHECKING:
    from litestar.config.app import AppConfig
__all__ = ["SQLAlchemyAsyncRepository", "SQLAlchemyAsyncSlugRepository", "on_app_init"]


def on_app_init(app_config: "AppConfig") -> "AppConfig":
    """Executes on application init.  Injects signature namespaces."""
    return _on_app_init(app_config)


class SQLAlchemyAsyncSlugRepository(
    SQLAlchemyAsyncRepository[ModelT],
):
    """Extends the repository to include slug model features.."""

    async def get_by_slug(
        self,
        slug: str,
        **kwargs: Any,
    ) -> ModelT | None:
        """Select record by slug value."""
        return await self.get_one_or_none(slug=slug)

    async def get_available_slug(
        self,
        value_to_slugify: str,
        **kwargs: Any,
    ) -> str:
        """Get a unique slug for the supplied value.

        If the value is found to exist, a random 4 digit character is appended to the end.  There may be a better way to do this, but I wanted to limit the number of additional database calls.

        Args:
            value_to_slugify (str): A string that should be converted to a unique slug.
            **kwargs: stuff

        Returns:
            str: a unique slug for the supplied value.  This is safe for URLs and other unique identifiers.
        """
        slug = slugify(value_to_slugify)
        if await self._is_slug_unique(slug):
            return slug
        random_string = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))  # noqa: S311
        return f"{slug}-{random_string}"

    async def _is_slug_unique(
        self,
        slug: str,
        **kwargs: Any,
    ) -> bool:
        return await self.get_one_or_none(slug=slug) is None
