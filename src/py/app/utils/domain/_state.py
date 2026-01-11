"""Discovery state and caching."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from litestar import Controller

logger = structlog.get_logger()


class DiscoveryCache:
    """Cache for discovered controllers to avoid re-discovery."""

    def __init__(self) -> None:
        self.controllers: list[type[Controller]] | None = None
        self.packages: set[str] = set()

    def clear(self) -> None:
        """Clear the cache."""
        self.controllers = None
        self.packages.clear()

    def is_cached(self, domain_packages: list[str]) -> bool:
        """Check if results for these packages are cached."""
        return self.controllers is not None and frozenset(domain_packages) <= self.packages

    def get(self) -> list[type[Controller]] | None:
        """Get cached controllers."""
        return self.controllers

    def set(self, controllers: list[type[Controller]], packages: list[str]) -> None:
        """Set cached controllers."""
        self.controllers = controllers
        self.packages.update(packages)


# Global cache instance
cache = DiscoveryCache()


class DiscoveryState:
    """Store discovery results for deferred logging during lifespan startup."""

    # Discovery results (populated during on_app_init)
    controller_count: int = 0
    controllers_by_domain: dict[str, list[str]] = {}
    signal_count: int = 0
    schema_count: int = 0
    service_count: int = 0
    repository_count: int = 0

    # Logging flags (prevent duplicate logs across app creations)
    logged_controllers: bool = False

    @classmethod
    def reset(cls) -> None:
        """Reset discovery state (for testing)."""
        cls.controller_count = 0
        cls.controllers_by_domain = {}
        cls.signal_count = 0
        cls.schema_count = 0
        cls.service_count = 0
        cls.repository_count = 0
        cls.logged_controllers = False

    @classmethod
    def log_discovery_results(cls) -> None:
        """Log discovery results (called during lifespan startup)."""
        if not cls.logged_controllers and cls.controller_count > 0:
            cls.logged_controllers = True
            try:
                # Try to pretty print if rich/structlog config allows, otherwise simple log
                logger.info(
                    "Discovered domain components",
                    controllers=cls.controller_count,
                    signals=cls.signal_count,
                    schemas=cls.schema_count,
                    services=cls.service_count,
                    repositories=cls.repository_count,
                    by_domain={k: sorted(v) for k, v in sorted(cls.controllers_by_domain.items())},
                )
            except Exception:  # noqa: BLE001
                logger.info(
                    "Discovered domain components",
                    controllers=cls.controller_count,
                    signals=cls.signal_count,
                    schemas=cls.schema_count,
                    services=cls.service_count,
                    repositories=cls.repository_count,
                )
