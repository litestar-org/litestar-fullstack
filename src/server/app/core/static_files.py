from starlite import StaticFilesConfig

from app.config import paths

config = [StaticFilesConfig(directories=[paths.PUBLIC_DIR], path=paths.urls.STATIC)]
"""Static files config"""
