"""Configuration for domain discovery."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DomainPluginConfig:
    """Configuration for domain auto-discovery plugin.

    Attributes:
        domain_packages: List of package paths containing domain subfolders.
            Each domain subfolder is scanned for controllers.
        discover_controllers: Whether to discover and register controllers.
        controller_submodules: Module/package names to search for controllers.
        log_discovered: Whether to log discovered components at startup.
    """

    domain_packages: list[str] = field(default_factory=lambda: ["app.domain"])
    discover_controllers: bool = True
    discover_signals: bool = True
    discover_schemas: bool = True
    discover_services: bool = True
    discover_repositories: bool = True

    controller_submodules: list[str] = field(default_factory=lambda: ["controllers", "routes", "controller", "route"])
    signal_submodules: list[str] = field(default_factory=lambda: ["signals", "events", "listeners"])
    schema_submodules: list[str] = field(default_factory=lambda: ["schemas", "models", "dtos"])
    service_submodules: list[str] = field(default_factory=lambda: ["services"])
    repository_submodules: list[str] = field(default_factory=lambda: ["repositories", "repos"])

    log_discovered: bool = True
