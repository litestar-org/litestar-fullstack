from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

import markupsafe
from jinja2 import TemplateNotFound as JinjaTemplateNotFound
from jinja2 import pass_context
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.exceptions import TemplateNotFoundException
from litestar.template.base import (
    TemplateEngineProtocol,
)

from .loader import ViteAssetLoader

if TYPE_CHECKING:
    from collections.abc import Callable

    from jinja2 import Template as JinjaTemplate
    from pydantic import DirectoryPath

    from app.contrib.vite.config import ViteConfig

T = TypeVar("T", bound=TemplateEngineProtocol)


class ViteTemplateEngine(JinjaTemplateEngine):
    """Jinja Template Engine with Vite Integration."""

    def __init__(self, directory: DirectoryPath | list[DirectoryPath], config: ViteConfig) -> None:
        """Jinja2 based TemplateEngine.

        Args:
            directory: Direct path or list of directory paths from which to serve templates.
            config: Vite config
        """
        super().__init__(directory=directory)
        self.config = config
        self.asset_loader = ViteAssetLoader.initialize_loader(config=self.config)
        self.engine.globals["vite_hmr_client"] = self.hmr_client
        self.engine.globals["vite_asset"] = self.resource

    def get_template(self, template_name: str) -> JinjaTemplate:
        """Retrieve a template by matching its name (dotted path) with files in the directory or directories provided.

        Args:
            template_name: A dotted path

        Returns:
            JinjaTemplate instance

        Raises:
            TemplateNotFoundException: if no template is found.
        """
        try:
            return self.engine.get_template(name=template_name)
        except JinjaTemplateNotFound as exc:
            raise TemplateNotFoundException(template_name=template_name) from exc

    def register_template_callable(self, key: str, template_callable: Callable[[dict[str, Any]], Any]) -> None:
        """Register a callable on the template engine.

        Args:
            key: The callable key, i.e. the value to use inside the template to call the callable.
            template_callable: A callable to register.

        Returns:
            None
        """
        self.engine.globals[key] = pass_context(template_callable)

    def hmr_client(self) -> markupsafe.Markup:
        """Generate the script tag for the Vite WS client for HMR.

        Only used when hot module reloading is enabled, in production this method returns an empty string.


        Returns:
            str: The script tag or an empty string.
        """
        tags: list = []
        tags.append(self.asset_loader.generate_react_hmr_tags())
        tags.append(self.asset_loader.generate_ws_client_tags())
        return markupsafe.Markup("".join(tags))

    def resource(self, path: str, scripts_attrs: dict[str, str] | None = None) -> markupsafe.Markup:
        """Generate all assets include tags for the file in argument.

        Generates all scripts tags for this file and all its dependencies
        (JS and CSS) by reading the manifest file (for production only).
        In development Vite imports all dependencies by itself.
        Place this tag in <head> section of your page
        (this function marks automatically <script> as "async" and "defer").

        Arguments:
            path: Path to a Vite asset to include.
            scripts_attrs: script attributes

        Keyword Arguments:
            scripts_attrs {Optional[Dict[str, str]]}: Override attributes added to scripts tags. (default: {None})

        Returns:
            str: All tags to import this asset in your HTML page.
        """
        return markupsafe.Markup(self.asset_loader.generate_asset_tags(path, scripts_attrs=scripts_attrs))
