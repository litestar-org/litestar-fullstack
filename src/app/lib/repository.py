import random
import string
from typing import Any

from starlite.contrib.sqlalchemy.repository import ModelT
from starlite.contrib.sqlalchemy.repository import SQLAlchemyRepository as _SQLAlchemyRepository

from app.utils import slugify


class SQLAlchemyRepository(_SQLAlchemyRepository[ModelT]):
    async def get_or_create(self, match_fields: list[str] | None = None, **kwargs: Any) -> tuple[ModelT, bool]:
        """Get instance identified by ``kwargs`` or create if it doesn't exist.

        Args:
            match_fields: a list of keys to use to match the existing model.  When empty, all fields are matched.
            **kwargs: Identifier of the instance to be retrieved.

        Returns:
            a tuple that includes the instance and whether or not it needed to be created.
        """
        if match_fields:
            match_filter = {
                field_name: kwargs.get(field_name, None)
                for field_name in match_fields
                if kwargs.get(field_name, None) is not None
            }
        else:
            match_filter = kwargs
        existing = await self.get_one_or_none(**match_filter)
        if existing:
            return existing, False
        return await self.add(self.model_type(**kwargs)), True  # type: ignore[arg-type]


class SQLAlchemySlugRepository(
    SQLAlchemyRepository[ModelT],
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
