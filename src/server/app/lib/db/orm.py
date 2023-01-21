"""Application ORM configuration."""

from __future__ import annotations

from starlite_saqlalchemy.db.orm import Base as DatabaseModel
from starlite_saqlalchemy.db.orm import meta

__all__ = ["DatabaseModel", "meta"]
