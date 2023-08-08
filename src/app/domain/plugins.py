from litestar.contrib.sqlalchemy.plugins.init.plugin import SQLAlchemyInitPlugin

from app.contrib.aiosql.plugin import AioSQLConfig, AioSQLPlugin
from app.contrib.saq.plugin import SAQConfig, SAQPlugin
from app.contrib.vite.config import ViteConfig
from app.contrib.vite.plugin import VitePlugin
from app.lib import db, settings
from app.lib.log import StructLogPlugin

aiosql = AioSQLPlugin(config=AioSQLConfig())
vite = VitePlugin(
    config=ViteConfig(
        static_dir=settings.STATIC_DIR,
        templates_dir=settings.TEMPLATES_DIR,
        hot_reload=settings.app.DEV_MODE,
        port=3005,
    )
)
saq = SAQPlugin(config=SAQConfig())
structlog = StructLogPlugin()
sqlalchemy = SQLAlchemyInitPlugin(config=db.config)
enabled_plugins = [structlog, aiosql, vite, sqlalchemy]
