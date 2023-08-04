from app.contrib.aiosql.plugin import AioSQLConfig, AioSQLPlugin
from app.contrib.saq.plugin import SAQConfig, SAQPlugin
from app.contrib.structlog.plugin import StructLogConfig, StructLogPlugin
from app.contrib.vite.config import ViteConfig
from app.contrib.vite.plugin import VitePlugin
from app.lib import settings

aiosql = AioSQLPlugin(config=AioSQLConfig())
vite = VitePlugin(
    config=ViteConfig(
        static_dir=settings.STATIC_DIR,
        templates_dir=settings.TEMPLATES_DIR,
        hot_reload=settings.app.DEV_MODE,
        port=3005,
    )
)
structlog = StructLogPlugin(config=StructLogConfig(logging_config=settings.log.config))
saq = SAQPlugin(config=SAQConfig())
