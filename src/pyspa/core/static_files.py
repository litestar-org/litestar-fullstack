from starlite import StaticFilesConfig

from pyspa.config import paths

config = [StaticFilesConfig(directories=[paths.PUBLIC_DIR, paths.ASSETS_DIR], path=paths.urls.STATIC)]
"""Static files config"""
