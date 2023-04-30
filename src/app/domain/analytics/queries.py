"""User Account Controllers."""
from __future__ import annotations

from pathlib import Path

import aiosql

from app.lib.settings import BASE_DIR

__all__ = ["analytics_queries"]


analytics_queries = aiosql.from_path(Path(BASE_DIR / "domain" / "analytics" / "sql"), driver_adapter="asyncpg")
