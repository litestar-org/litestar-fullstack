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

``tools/deploy/railway/deploy.sh`` provisions a cost-effective single-service deployment by default:
PostgreSQL connected over Railway's private network (``DATABASE_PRIVATE_URL`` for zero egress cost)
plus one distroless API service running ``QUEUES_PLACEMENT=asgi`` (embedding the ``litestar-queues``
worker inside the ASGI lifespan with automatic terminal-task pruning via
``QUEUES_TERMINAL_RETENTION_SECONDS=604800``). ``railway.app.json`` runs
``app database upgrade --no-prompt`` as a ``preDeployCommand`` before traffic cutover and scopes
rebuilds with ``watchPatterns``. Pass ``--dedicated-worker`` to ``deploy.sh`` when scaling horizontally
with ``railway.worker.json`` and ``QUEUES_PLACEMENT=external``.

Kubernetes
----------

``tools/deploy/k8s/deploy.py`` renders Jinja2 manifests for the API deployment, standalone
``app queues run`` worker deployment with HPA, PostgreSQL, Ingress, ConfigMap, Secrets, and
optional PodDisruptionBudget.
