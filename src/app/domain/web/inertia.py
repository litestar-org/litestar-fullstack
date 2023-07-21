from __future__ import annotations

from app.contrib.vite.template_engine import ViteTemplateEngine

__all__ = ["InertiaTemplateEngine"]


class InertiaTemplateEngine(ViteTemplateEngine):
    """Inertia Extensions for rendering the inertia data."""

    def page_props(self) -> None:
        """Render page props to inertia template."""
