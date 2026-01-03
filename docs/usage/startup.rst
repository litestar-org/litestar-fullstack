===================
Starting the server
===================

This section describes how to start the application in development and production mode.

Development
^^^^^^^^^^^

Set ``VITE_DEV_MODE=true`` to enable the Vite dev server, then run:

.. code-block:: bash

    uv run app run

This starts the Litestar API, SAQ workers (if ``SAQ_USE_SERVER_LIFESPAN`` is enabled),
and the Vite dev server. Assets are served under ``/static/web/`` and the dev server
listens on ``VITE_PORT`` (default ``3006``) when set.

Production
^^^^^^^^^^

Build the frontend assets into ``src/py/app/server/static/web``:

.. code-block:: bash

    uv run app assets build

Then run the server with ``VITE_DEV_MODE=false`` (or unset):

.. code-block:: bash

    uv run app run

.. note::
   - ``VITE_DEV_MODE``: Enable the Vite dev server.
   - ``VITE_PORT``: Optional dev server port override.
   - ``ASSET_URL``: Optional asset base path (defaults to ``/static/web/``).
   - ``SAQ_USE_SERVER_LIFESPAN``: Auto start/stop SAQ processes with the app.
