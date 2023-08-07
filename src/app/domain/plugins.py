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
structlog = StructLogPlugin(
    config=StructLogConfig(
        loggers={
            "uvicorn.access": {
                "propagate": False,
                "level": settings.log.UVICORN_ACCESS_LEVEL,
                "handlers": ["queue_listener"],
            },
            "uvicorn.error": {
                "propagate": False,
                "level": settings.log.UVICORN_ERROR_LEVEL,
                "handlers": ["queue_listener"],
            },
            "saq": {
                "propagate": False,
                "level": settings.log.SAQ_LEVEL,
                "handlers": ["queue_listener"],
            },
            "sqlalchemy.engine": {
                "propagate": False,
                "level": settings.log.SQLALCHEMY_LEVEL,
                "handlers": ["queue_listener"],
            },
            "sqlalchemy.pool": {
                "propagate": False,
                "level": settings.log.SQLALCHEMY_LEVEL,
                "handlers": ["queue_listener"],
            },
        },
    )
)
saq = SAQPlugin(config=SAQConfig())

enabled_plugins = [aiosql, vite, structlog]
