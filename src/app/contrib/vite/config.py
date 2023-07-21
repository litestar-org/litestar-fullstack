from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from inspect import isclass
from typing import TYPE_CHECKING, Generic, TypeVar, cast

from litestar.exceptions import ImproperlyConfiguredException
from litestar.template import TemplateEngineProtocol

__all__ = ["ViteConfig", "ViteTemplateConfig"]


if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from litestar.types import PathType

    from .template_engine import ViteTemplateEngine

T = TypeVar("T", bound=TemplateEngineProtocol)


@dataclass
class ViteConfig:
    """Configuration for ViteJS support.

    To enable Vite integration, pass an instance of this class to the
    :class:`Litestar <litestar.app.Litestar>` constructor using the
    'plugins' key.
    """

    static_dir: Path
    """Location of the manifest file.

    The path relative to the `static_url` location
    """
    templates_dir: Path
    """Location of the Jinja2 template file.
    """
    manifest_name: str = "manifest.json"
    """Name of the manifest file."""
    hot_reload: bool = False
    """Enable HMR for Vite development server."""
    is_react: bool = False
    """Enable React components."""
    static_url: str = "/static/"
    """Base URL to generate for static asset references.

    This should match what you have for the STATIC_URL
    """
    host: str = "localhost"
    """Default host to use for Vite server."""
    protocol: str = "http"
    """Protocol to use for communication"""
    port: int = 3000
    """Default port to use for Vite server."""
    run_command: str = "npm run dev"
    """Default command to use for running Vite."""
    build_command: str = "npm run build"


@dataclass
class ViteTemplateConfig(Generic[T]):
    """Configuration for Templating.

    To enable templating, pass an instance of this class to the
    :class:`Litestar <litestar.app.Litestar>` constructor using the
    'template_config' key.
    """

    engine: type[ViteTemplateEngine]
    """A template engine adhering to the :class:`TemplateEngineProtocol
    <litestar.template.base.TemplateEngineProtocol>`."""
    config: ViteConfig
    """A a config for the vite engine`."""
    directory: PathType | None = field(default=None)
    """A directory or list of directories from which to serve templates."""
    engine_callback: Callable[[T], None] | None = field(default=None)
    """A callback function that allows modifying the instantiated templating
    protocol."""

    def __post_init__(self) -> None:
        """Ensure that directory is set if engine is a class."""
        if isclass(self.engine) and not self.directory:
            raise ImproperlyConfiguredException("directory is a required kwarg when passing a template engine class")

    def to_engine(self) -> T:
        """Instantiate the template engine."""
        template_engine = cast("T", self.engine(self.directory, self.config) if isclass(self.engine) else self.engine)
        if callable(self.engine_callback):
            self.engine_callback(template_engine)
        return template_engine

    @cached_property
    def engine_instance(self) -> T:
        """Return the template engine instance."""
        return self.to_engine()
