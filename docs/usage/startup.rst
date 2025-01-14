===================
Starting the server
===================

This section describes how to start the server in development and production mode.

Development
^^^^^^^^^^^

If ``VITE_DEV_MODE`` and ``VITE_USE_SERVER_LIFESPAN`` are both set  to true, the `run` command will automatically start `vite` during the ``server_lifespan`` startup hook of the Litestar CLI.

Additionally, when you start the application with ``VITE_HOT_RELOAD`` set to true, it will also enable the HMR websocket connection to Vite.  This will allow the main Granian (or Uvicorn) web server to support Vite's hot reload functionality.


.. dropdown:: Starting the server in dev mode

  .. code-block:: bash

      (.venv) cody@localtop:~/Code/Litestar/litestar-fullstack$ uv run app run -p 8089
      Using Litestar app from env: 'app.asgi:app'
      Loading environment configuration from .env
      Starting Granian server process ───────────────────────────────────────────────────────
      ┌──────────────────────────────┬──────────────────────────────────────────────────────┐
      │ Litestar version             │ 2.8.2                                                │
      │ Debug mode                   │ Enabled                                              │
      │ Python Debugger on exception │ Disabled                                             │
      │ CORS                         │ Enabled                                              │
      │ CSRF                         │ Disabled                                             │
      │ OpenAPI                      │ Enabled path=/schema                                 │
      │ Compression                  │ Disabled                                             │
      │ Template engine              │ ViteTemplateEngine                                   │
      │ Middlewares                  │ JWTCookieAuthenticationMiddleware, LoggingMiddleware │
      └──────────────────────────────┴──────────────────────────────────────────────────────┘
      Starting Vite process with HMR Enabled ────────────────────────────────────────────────
      Starting SAQ Workers ──────────────────────────────────────────────────────────────────

      > dev
      > vite

      [INFO] Starting granian (main PID: 55642)
      [INFO] Listening at: http://0.0.0.0:8089
      [INFO] Spawning worker-1 with pid: 55689

        VITE v5.2.9  ready in 273 ms

        ➜  Local:   http://localhost:5174/static/
        ➜  Network: http://10.23.18.75:5174/static/
        ➜  press h + enter to show help

        LITESTAR   plugin v0.5.1

        ➜  APP_URL: http://localhost:8089
      Loading environment configuration from .env
      [INFO] Started worker-1
      [INFO] Started worker-1 runtime-1


Production
^^^^^^^^^^

If ``VITE_DEV_MODE`` is false, the server will look for the static assets that are produced from the ``npm run build`` command.
This command is automatically executed and the assets are bundled when running ``uv build``.

To manually rebuild assets, use the following:

.. code-block:: bash
  :caption: Generates static assets from Vite and runs the application.

    (.venv) cody@localtop:~/Code/Litestar/litestar-fullstack$ app assets build
    Using Litestar app from env: 'app.asgi:app'
    Loading environment configuration from .env
    Starting Vite build process ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

    > build
    > vite build

    vite v5.2.9 building for production...
    ✓ 222 modules transformed.
    src/app/domain/web/public/manifest.json                  0.53 kB │ gzip:   0.22 kB
    src/app/domain/web/public/assets/favicon-DXHXvpft.png    7.69 kB
    src/app/domain/web/public/assets/main-D9hDRSjL.css      34.22 kB │ gzip:   6.88 kB
    src/app/domain/web/public/assets/main-gDMW9BNa.js       41.96 kB │ gzip:  10.46 kB
    src/app/domain/web/public/assets/vendor-DcvSTexI.js    493.83 kB │ gzip: 155.51 kB
    ✓ built in 2.91s
    Assets built.

.. dropdown:: Starting the server in production mode

  .. code-block:: bash

      (.venv) cody@localtop:~/Code/Litestar/litestar-fullstack$ app run -p 8089
      Using Litestar app from env: 'app.asgi:app'
      Loading environment configuration from .env
      Starting Granian server process ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
      ┌──────────────────────────────┬──────────────────────────────────────────────────────┐
      │ Litestar version             │ 2.8.2                                                │
      │ Debug mode                   │ Enabled                                              │
      │ Python Debugger on exception │ Disabled                                             │
      │ CORS                         │ Enabled                                              │
      │ CSRF                         │ Disabled                                             │
      │ OpenAPI                      │ Enabled path=/schema                                 │
      │ Compression                  │ Disabled                                             │
      │ Template engine              │ ViteTemplateEngine                                   │
      │ Middlewares                  │ JWTCookieAuthenticationMiddleware, LoggingMiddleware │
      └──────────────────────────────┴──────────────────────────────────────────────────────┘
      Serving assets using manifest at `/home/cody/Code/Litestar/litestar-fullstack/src/app/domain/web/public/manifest.json`. ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
      Starting SAQ Workers ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
      [INFO] Starting granian (main PID: 47755)
      [INFO] Listening at: http://0.0.0.0:8089
      [INFO] Spawning worker-1 with pid: 47760
      Loading environment configuration from .env
      [INFO] Started worker-1
      [INFO] Started worker-1 runtime-1

.. note::
   - ``VITE_DEV_MODE``: Enables the Vite development server when set to true.
   - ``VITE_USE_SERVER_LIFESPAN``: Automatically starts and stops Vite processes during the server lifespan in development mode.
   - ``VITE_HOT_RELOAD``: Enables hot module reloading (HMR) with Vite when set to true.
   - ``SAQ_USE_SERVER_LIFESPAN``: Automatically starts and stops SAQ workers during the server lifespan in development mode.
