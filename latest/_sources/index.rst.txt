==================
Litestar Fullstack
==================

Litestar Fullstack is a production-ready reference application demonstrating the first-party
Litestar plugin ecosystem with PostgreSQL (``asyncpg``), React 19, Vite, and ``uv_build``.

.. seealso:: Built with `Litestar <https://litestar.dev>`_, `Advanced Alchemy <https://advanced-alchemy.litestar.dev/>`_,
  `litestar-security <https://github.com/litestar-org/litestar-security>`_,
  `litestar-queues <https://github.com/cofin/litestar-queues>`_,
  `litestar-autowire <https://github.com/cofin/litestar-autowire>`_,
  `litestar-mcp <https://github.com/cofin/litestar-mcp>`_,
  `litestar-asyncapi <https://github.com/cofin/litestar-asyncapi>`_,
  `litestar-vite <https://github.com/cofin/litestar-vite>`_,
  `litestar-email <https://github.com/cofin/litestar-email>`_, and
  `litestar-granian <https://github.com/cofin/litestar-granian>`_:

  - React 19 SPA with TanStack Router, TanStack Query, Tailwind CSS v4, and generated OpenAPI/AsyncAPI types
  - Fail-closed cookie session authentication with CSRF, TOTP MFA, WebAuthn Passkeys, OAuth2/OIDC, and API keys
  - PostgreSQL-backed background queues with ``LISTEN``/``NOTIFY`` wakeups and live SSE/WebSocket task streaming
  - Authenticated MCP JSON-RPC endpoint for safe workspace resources and tools
  - Postgres-only Docker, Railway, and Kubernetes deployment blueprints

Installation
------------

Follow :doc:`the installation guide <usage/installation>` to set up your environment.

Usage
-----

Explore the operational guides in :doc:`usage/index`.

Reference
---------

Browse the Python module reference in :doc:`api/index`.

.. toctree::
    :titlesonly:
    :caption: Documentation
    :hidden:

    usage/index
    api/index

.. toctree::
    :titlesonly:
    :caption: Development
    :hidden:

    contribution-guide
    changelog
