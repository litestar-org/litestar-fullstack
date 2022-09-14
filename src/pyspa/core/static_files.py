from pathlib import Path

from starlite import StaticFilesConfig

from pyspa.config import paths

config = [
    StaticFilesConfig(
        directories=[Path(paths.BASE_DIR, "web/public"), Path(paths.BASE_DIR, "web/assets")], path="/public"
    ),
]
"""Static files config"""
