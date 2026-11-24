==========
Deployment
==========

The application requires only PostgreSQL at runtime—sessions, rate limiting, security tokens, and
background queues all persist in PostgreSQL tables.

Docker
------

Multi-stage Dockerfiles live under ``tools/deploy/docker/``:

- ``Dockerfile`` — Python 3.13 slim API runtime built from the ``uv_build`` wheel with embedded static SPA and React Email assets.
- ``Dockerfile.distroless`` — hardened distroless API image.
- ``Dockerfile.worker`` — dedicated ``app queues run`` worker image (includes compiled email templates, excludes SPA assets).
- ``Dockerfile.dev`` — hot-reload development image.

Railway
-------

``tools/deploy/railway/deploy.sh`` provisions PostgreSQL, the API service, and a standalone
``Queue Worker`` service running ``app queues run`` with ``QUEUES_PLACEMENT=external`` and
``LITESTAR_TRUSTED_PROXIES=*``. Schedule periodic maintenance via a Railway cron job running
``app queues run-maintenance --json``.

Kubernetes
----------

``tools/deploy/k8s/deploy.py`` renders Jinja2 manifests for the API deployment, standalone
``app queues run`` worker deployment with HPA, PostgreSQL, Ingress, ConfigMap, Secrets, and
optional PodDisruptionBudget.
