from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar
from urllib.parse import urljoin

from litestar.template import TemplateEngineProtocol

if TYPE_CHECKING:
    from app.contrib.vite import ViteConfig

T = TypeVar("T", bound=TemplateEngineProtocol)


class ViteAssetLoader:
    """Vite  manifest loader.

    Please see: https://vitejs.dev/guide/backend-integration.html
    """

    _instance: ClassVar[ViteAssetLoader | None] = None

    def __init__(self, config: ViteConfig) -> None:
        self._config = config
        self._manifest: dict[str, Any] = {}

    @classmethod
    def initialize_loader(cls, config: ViteConfig) -> ViteAssetLoader:
        """Singleton manifest loader."""
        if cls._instance is None:
            cls._instance = cls(config=config)
            cls._instance.parse_manifest()
        return cls._instance

    def parse_manifest(self) -> None:
        """Read and parse the Vite manifest file.

        Example manifest:
        ```json
            {
                "main.js": {
                    "file": "assets/main.4889e940.js",
                    "src": "main.js",
                    "isEntry": true,
                    "dynamicImports": ["views/foo.js"],
                    "css": ["assets/main.b82dbe22.css"],
                    "assets": ["assets/asset.0ab0f9cd.png"]
                },
                "views/foo.js": {
                    "file": "assets/foo.869aea0d.js",
                    "src": "views/foo.js",
                    "isDynamicEntry": true,
                    "imports": ["_shared.83069a53.js"]
                },
                "_shared.83069a53.js": {
                    "file": "assets/shared.83069a53.js"
                }
                }
        ```

        Raises:
            RuntimeError: if cannot load the file or JSON in file is malformed.
        """

        if not self._config.hot_reload:
            with Path(self._config.static_dir / self._config.manifest_name).open() as manifest_file:
                manifest_content = manifest_file.read()
            try:
                self._manifest = json.loads(manifest_content)
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError(
                    "Cannot read Vite manifest file at %s",
                    Path(self._config.static_dir / self._config.manifest_name),
                ) from exc

    def generate_ws_client_tags(self) -> str:
        """Generate the script tag for the Vite WS client for HMR.

        Only used when hot module reloading is enabled, in production this method returns an empty string.

        Returns:
            str: The script tag or an empty string.
        """
        if not self._config.hot_reload:
            return ""

        return self._script_tag(
            self._vite_server_url("@vite/client"),
            {"type": "module"},
        )

    def generate_react_hmr_tags(self) -> str:
        """Generate the script tag for the Vite WS client for HMR.

        Only used when hot module reloading is enabled, in production this method returns an empty string.

        Returns:
            str: The script tag or an empty string.
        """
        if self._config.is_react and self._config.hot_reload:
            return f"""
                <script type="module">
                import RefreshRuntime from '{self._vite_server_url()}@react-refresh'
                RefreshRuntime.injectIntoGlobalHook(window)
                window.$RefreshReg$ = () => {{}}
                window.$RefreshSig$ = () => (type) => type
                window.__vite_plugin_react_preamble_installed__=true
                </script>
                """
        return ""

    def generate_asset_tags(self, path: str, scripts_attrs: dict[str, str] | None = None) -> str:
        """Generate all assets include tags for the file in argument.

        Returns:
            str: All tags to import this asset in your HTML page.
        """
        if self._config.hot_reload:
            return self._script_tag(
                self._vite_server_url(path),
                {"type": "module", "async": "", "defer": ""},
            )

        if path not in self._manifest:
            raise RuntimeError(
                "Cannot find %s in Vite manifest at %s",
                path,
                Path(self._config.static_dir / self._config.manifest_name),
            )

        tags = []
        manifest_entry: dict = self._manifest[path]
        if not scripts_attrs:
            scripts_attrs = {"type": "module", "async": "", "defer": ""}

        # Add dependent CSS
        if "css" in manifest_entry:
            for css_path in manifest_entry.get("css", {}):
                tags.append(self._style_tag(urljoin(self._config.static_url, css_path)))

        # Add dependent "vendor"
        if "imports" in manifest_entry:
            for vendor_path in manifest_entry.get("imports", {}):
                tags.append(self.generate_asset_tags(vendor_path, scripts_attrs=scripts_attrs))

        # Add the script by itself
        tags.append(
            self._script_tag(
                urljoin(self._config.static_url, manifest_entry["file"]),
                attrs=scripts_attrs,
            ),
        )

        return "".join(tags)

    def _vite_server_url(self, path: str | None = None) -> str:
        """Generate an URL to and asset served by the Vite development server.

        Keyword Arguments:
            path: Path to the asset. (default: {None})

        Returns:
            str: Full URL to the asset.
        """
        base_path = f"{self._config.protocol}://{self._config.host}:{self._config.port}"
        return urljoin(
            base_path,
            urljoin(self._config.static_url, path if path is not None else ""),
        )

    def _script_tag(self, src: str, attrs: dict[str, str] | None = None) -> str:
        """Generate an HTML script tag."""
        attrs_str = ""
        if attrs is not None:
            attrs_str = " ".join([f'{key}="{value}"' for key, value in attrs.items()])

        return f'<script {attrs_str} src="{src}"></script>'

    def _style_tag(self, href: str) -> str:
        """Generate and HTML <link> stylesheet tag for CSS.

        Args:
            href: CSS file URL.

        Returns:
            str: CSS link tag.
        """
        return f'<link rel="stylesheet" href="{href}" />'
