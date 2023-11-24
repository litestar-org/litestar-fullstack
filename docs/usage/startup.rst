===================
Starting the server
===================

This section describes how to start the server in development and production mode.

Development
^^^^^^^^^^^

If ``DEV_MODE`` is set to true, the base template expects that Vite will be running.
When you start the application, it will try to start the Vite service with the HMR websocket connection enabled.


.. dropdown:: Starting the server in dev mode

  .. code-block:: bash

      ❯ app run-all -p 8080
      Using Litestar app from env: 'app.asgi:create_app'
      2023-10-01T20:19:06.493377Z [info     ] starting all application services.
      2023-10-01T20:19:06.493500Z [info     ] starting Background worker processes.
      2023-06-16T16:58:38.055247Z [info     ] starting Vite
      2023-06-16T16:58:38.056850Z [info     ] Starting HTTP Server.
      2023-06-16T16:58:38.791943Z [info     ] Started server process [29108]
      2023-06-16T16:58:38.792012Z [info     ] Waiting for application startup.
      2023-06-16T16:58:38.794260Z [info     ] Application startup complete.
      2023-06-16T16:58:38.794876Z [info     ] Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
      2023-06-16T16:58:38.803751Z [info     ] Starting working pool
      2023-06-16T16:58:38.804423Z [info     ] Worker is starting up.
      2023-06-16T16:58:38.804519Z [info     ] Worker is starting up.
      2023-06-16T16:58:38.816324Z [info     ] Performing background worker task.
      2023-06-16T16:58:39.188218Z [info     ] Vite                           message=> litestar-fullstack@0.0.0 dev> vite
      2023-06-16T16:58:39.894411Z [info     ] Vite                           message=Forced re-optimization of dependencies
      2023-06-16T16:58:39.923813Z [info     ] Vite                           message=  VITE v4.3.9  ready in 676 ms
      2023-06-16T16:58:39.924023Z [info     ] Vite                           message=  ➜  Local:   http://localhost:3000/static/  ➜  Network: use ^host to expose

Production
^^^^^^^^^^

If ``DEV_MODE`` is false, the server will look for the static assets that are produced from the ``npm run build`` command.
This command is automatically executed and the assets are bundled when running ``pdm build``.

To manually rebuild assets, use the following:

.. code-block:: bash
  :caption: Generates static assets from Vite and runs the application.

    npm run build
    # files from the above command can be found in 'src/app/domain/web/public'
    app run-all

.. dropdown:: Starting the server in production mode

  .. code-block:: bash

      ❯ npm run build

      > litestar-fullstack@0.0.0 build
      > vue-tsc && vite build

      vite v4.1.2 building for production...
      ✓ 15 modules transformed.
      Generated an empty chunk: "vue".
      ../public/assets/vue-5532db34.svg    0.50 kB
      ../public/manifest.json              0.57 kB
      ../public/assets/main-b75adab1.css   1.30 kB │ gzip:  0.67 kB
      ../public/assets/vue-4ed993c7.js     0.00 kB │ gzip:  0.02 kB
      ../public/assets/main-17f9b70b.js    1.50 kB │ gzip:  0.80 kB
      ../public/assets/@vue-5be96905.js   52.40 kB │ gzip: 21.07 kB

      ❯ app run-all
      2023-02-19 22:53:08 [info     ] starting application.
      2023-02-19 22:53:08 [info     ] starting Background worker processes.
      2023-02-19 22:53:08 [info     ] Starting HTTP Server.
