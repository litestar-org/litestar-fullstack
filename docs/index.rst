==================
Litestar Fullstack
==================

The Litestar Fullstack repository contains the reference code for a fully-capable, production-ready
fullstack Litestar web application. It is intended to be used as a starting point for new projects
and as a reference for how to build a large scale fullstack Litestar application.

You can take pieces as needed, or use the entire thing as a starting point for your project.
It includes the following capabilities out of the box:

.. seealso:: It is built on the `Litestar <https://litestar.dev>`_, React, `Vite <https://vitejs.dev/>`_,
  :doc:`SAQ <saq:index>`, `TailwindCSS <https://tailwindcss.com/>`_, and
  :doc:`Advanced Alchemy <advanced-alchemy:index>` with features to reference:

  - SPA frontend with React 19 and Vite (SPA mode via `litestar-vite <https://github.com/cofin/litestar-vite>`_)
  - JWT auth with refresh tokens, MFA, OAuth, and admin tooling
  - Service/repository pattern with UUIDv7 primary keys
  - Background jobs via :doc:`SAQ <saq:index>` and structured logging with :doc:`structlog <structlog:index>`
  - Dockerized development and production workflows
  - Test suite for backend features

Installation
------------

To get started, check out :doc:`the installation guide <usage/installation>`.

Usage
-----

To see how to use the Litestar Fullstack, check out :doc:`the usage guide <usage/index>`.

Reference
---------

We also provide an API reference which can be found at :doc:`api/index`.

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
