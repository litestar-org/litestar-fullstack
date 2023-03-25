from __future__ import annotations

from typing import TYPE_CHECKING

from .vite import ViteTemplateEngine

__all__ = ["InertiaTemplateEngine"]


if TYPE_CHECKING:
    from pydantic import DirectoryPath


class InertiaTemplateEngine(ViteTemplateEngine):
    """Inertia Extensions for rendering the inertia data."""

    def __init__(self, directory: DirectoryPath | list[DirectoryPath]) -> None:
        """Implement inertia templates with the default JinjaTemplateEngine."""
        super().__init__(directory)

    def page_props(self) -> None:
        """Render page props to inertia template."""
