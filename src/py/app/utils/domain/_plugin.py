"""Domain discovery plugin implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.utils.domain._config import DomainPluginConfig
from app.utils.domain._discovery import (
    discover_domain_controllers,
    discover_domain_repositories,
    discover_domain_schemas,
    discover_domain_services,
    discover_domain_signals,
)
from app.utils.domain._state import DiscoveryState

if TYPE_CHECKING:
    from litestar import Controller
    from litestar.config.app import AppConfig

logger = structlog.get_logger()


class DomainPlugin:
    """Litestar plugin for automatic domain discovery.

    Discovers and registers:
    - Controller classes from domain.*.controllers/
    - Signals/Listeners from domain.*.signals/
    - Schemas from domain.*.schemas/ (for signature namespace)
    - Services from domain.*.services/ (for signature namespace)
    - Repositories from domain.*.repositories/ (for signature namespace)

    This plugin implements Litestar's InitPluginProtocol to integrate with
    the application initialization lifecycle.
    """

    __slots__ = ("config",)

    def __init__(self, config: DomainPluginConfig | None = None) -> None:
        """Initialize the domain plugin.

        Args:
            config: Plugin configuration. If None, uses defaults.
        """
        self.config = config or DomainPluginConfig()

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        """Initialize the plugin when app is created.

        This method is called by Litestar during application initialization.
        It discovers controllers based on the plugin configuration.

        Args:
            app_config: The Litestar application configuration.

        Returns:
            The modified application configuration.
        """
        if self.config.discover_controllers:
            self._discover_and_register_controllers(app_config)

        if self.config.discover_signals:
            self._discover_and_register_signals(app_config)

        if self.config.discover_schemas:
            self._discover_and_register_schemas(app_config)

        if self.config.discover_services:
            self._discover_and_register_services(app_config)

        if self.config.discover_repositories:
            self._discover_and_register_repositories(app_config)

        # Register startup hook for deferred logging
        if self.config.log_discovered:
            app_config.on_startup = app_config.on_startup or []
            app_config.on_startup.insert(0, _on_startup_log_discovery)

        return app_config

    def _discover_and_register_controllers(self, app_config: AppConfig) -> None:
        """Discover controllers and register them with the application.

        Args:
            app_config: The application configuration to update.
        """
        controllers = discover_domain_controllers(self.config.domain_packages, self.config.controller_submodules)

        if not controllers:
            logger.warning("No controllers discovered", domain_packages=self.config.domain_packages)
            return

        # Store results for deferred logging
        self._store_controller_results(controllers)

        app_config.route_handlers.extend(controllers)

    def _discover_and_register_signals(self, app_config: AppConfig) -> None:
        """Discover and register signals/listeners.

        Args:
            app_config: The application configuration to update.
        """
        signals = discover_domain_signals(self.config.domain_packages, self.config.signal_submodules)
        if signals:
            app_config.listeners.extend(signals)
            DiscoveryState.signal_count = len(signals)

    def _discover_and_register_schemas(self, app_config: AppConfig) -> None:
        """Discover and register schemas for signature namespace.

        Args:
            app_config: The application configuration to update.
        """
        schemas = discover_domain_schemas(self.config.domain_packages, self.config.schema_submodules)
        if schemas:
            app_config.signature_namespace.update(schemas)
            DiscoveryState.schema_count = len(schemas)

    def _discover_and_register_services(self, app_config: AppConfig) -> None:
        """Discover and register services for signature namespace.

        Args:
            app_config: The application configuration to update.
        """
        services = discover_domain_services(self.config.domain_packages, self.config.service_submodules)
        if services:
            app_config.signature_namespace.update(services)
            DiscoveryState.service_count = len(services)

    def _discover_and_register_repositories(self, app_config: AppConfig) -> None:
        """Discover and register repositories for signature namespace.

        Args:
            app_config: The application configuration to update.
        """
        repositories = discover_domain_repositories(self.config.domain_packages, self.config.repository_submodules)
        if repositories:
            app_config.signature_namespace.update(repositories)
            DiscoveryState.repository_count = len(repositories)

    def _store_controller_results(self, controllers: list[type[Controller]]) -> None:
        """Store controller discovery results for deferred logging.

        Args:
            controllers: List of discovered controller classes.
        """
        by_domain: dict[str, list[str]] = {}
        for ctrl in controllers:
            module = getattr(ctrl, "__module__", "unknown")
            parts = module.split(".")
            # Estimate domain name from module path (e.g. app.domain.accounts.controllers -> accounts)
            try:
                domain_idx = parts.index("domain")
                domain = parts[domain_idx + 1] if len(parts) > domain_idx + 1 else "unknown"
            except ValueError:
                domain = "unknown"

            if domain not in by_domain:
                by_domain[domain] = []
            by_domain[domain].append(ctrl.__name__)

        DiscoveryState.controller_count = len(controllers)
        DiscoveryState.controllers_by_domain = by_domain


def _on_startup_log_discovery() -> None:
    """Lifespan startup hook to log discovery results after server header."""
    DiscoveryState.log_discovery_results()
