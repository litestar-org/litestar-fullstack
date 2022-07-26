from pyspa.config.application import settings
from pyspa.config.logging import log_config

# Gunicorn config variables
accesslog = settings.gunicorn.ACCESS_LOG
bind = f"{settings.gunicorn.HOST}:{settings.gunicorn.PORT}"
errorlog = settings.gunicorn.ERROR_LOG
keepalive = settings.gunicorn.KEEPALIVE
logconfig_dict = log_config.dict(exclude_none=True)
loglevel = settings.gunicorn.LOG_LEVEL
reload = settings.gunicorn.RELOAD
threads = settings.gunicorn.THREADS
timeout = settings.gunicorn.TIMEOUT
worker_class = settings.gunicorn.WORKER_CLASS
workers = settings.gunicorn.WORKERS
