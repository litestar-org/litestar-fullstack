===================
Starting the Server
===================

Development
-----------

With ``VITE_DEV_MODE=true`` and ``QUEUES_PLACEMENT=asgi`` in ``.env``, start the Litestar API
(served by Granian), in-process queue worker, and Vite dev server together:

.. code-block:: bash

    uv run app run

Assets are served under ``/static/web/`` and the Vite dev server binds to ``VITE_PORT`` (default ``3006``).

Production
----------

Build static email templates and SPA assets (regenerating OpenAPI/AsyncAPI types first):

.. code-block:: bash

    make build-emails
    make build-assets

Start the API server with ``VITE_DEV_MODE=false`` and ``QUEUES_PLACEMENT=external``:

.. code-block:: bash

    uv run app run

Run one or more dedicated queue worker processes:

.. code-block:: bash

    uv run app queues run

Key Environment Variables
-------------------------

- ``DATABASE_URL``: ``postgresql+asyncpg://...`` connection string.
- ``QUEUES_PLACEMENT``: ``asgi`` (in-process dev worker) or ``external`` (dedicated ``app queues run`` worker).
- ``QUEUES_MAX_CONCURRENCY`` / ``QUEUES_POLL_INTERVAL``: Worker concurrency and fallback poll interval.
- ``LITESTAR_TRUSTED_PROXIES``: Comma-separated trusted proxy CIDR/host list (or ``*`` behind managed load balancers).
- ``VITE_DEV_MODE`` / ``VITE_PORT`` / ``ASSET_URL``: Vite integration settings.
