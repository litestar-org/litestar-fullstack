===========
Development
===========

Common tasks are exposed through the root ``Makefile``.

Core Commands
-------------

- ``make install`` — sync Python and Bun dependencies across ``src/js/web`` and ``src/js/templates``.
- ``make upgrade`` — update ``uv.lock``, Bun dependencies, and pre-commit hooks.
- ``make types`` — export OpenAPI and AsyncAPI schemas and regenerate the TypeScript SDK (gitignored under ``src/js/web/src/lib/generated``).
- ``make build-emails`` — compile React Email templates into ``src/py/app/server/static/email``.
- ``make lint`` — run Ruff, Mypy, Pyright, Slotscheck, and Codespell.
- ``make frontend-check`` — run Biome lint checks and Vitest tests in ``src/js/web``.
- ``make test`` — execute pytest with ``pytest-databases`` PostgreSQL template database cloning.
- ``make build-wheel`` — compile emails, frontend SPA assets, and the ``uv_build`` wheel in ``dist/``.
- ``make docs`` — build Sphinx documentation strictly with ``-W --keep-going``.

Database Migrations
-------------------

Create or apply migrations via the ``app`` CLI:

.. code-block:: bash

    uv run app database make-migrations
    uv run app database upgrade

Full Makefile
-------------

.. dropdown:: Full Makefile

    .. literalinclude:: ../../Makefile
        :language: make
