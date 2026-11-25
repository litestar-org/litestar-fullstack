"""Database-backed rate limiting using ``litestar-security`` ``StoreRateLimiter`` and Advanced Alchemy ``SQLAlchemyStore``."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from advanced_alchemy.extensions.litestar.store import SQLAlchemyStore
from litestar_security.accounts import RateLimiter, RateLimitPolicy, StoreRateLimiter
from litestar_security.accounts._rate_limits import DEFAULT_RATE_LIMIT_POLICIES

from app.db import models as m

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

__all__ = ("build_rate_limiter",)


def build_rate_limiter(
    alchemy_config: SQLAlchemyAsyncConfig,
    *,
    policies: Mapping[str, RateLimitPolicy] | None = None,
    clock: Callable[[], datetime] | None = None,
) -> RateLimiter:
    """Construct a database-backed ``StoreRateLimiter`` over Advanced Alchemy's ``SQLAlchemyStore``.

    Args:
        alchemy_config: Shared Advanced Alchemy async configuration.
        policies: Optional per-operation rate-limit budgets; defaults to ``litestar-security`` policies.
        clock: Optional UTC clock callable for deterministic testing.

    Returns:
        Configured ``RateLimiter`` backed by the ``app_store`` table.
    """
    store = SQLAlchemyStore(config=alchemy_config, model=m.AppStore, namespace="rate_limit")
    return StoreRateLimiter(
        policies=policies if policies is not None else DEFAULT_RATE_LIMIT_POLICIES,
        store=store,
        clock=clock if clock is not None else (lambda: datetime.now(UTC)),
    )
