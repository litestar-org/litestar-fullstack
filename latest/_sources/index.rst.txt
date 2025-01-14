==================
Litestar Fullstack
==================

The Litestar Fullstack repository contains the reference code for a fully-capable, production-ready
fullstack Litestar web application. It is intended to be used as a starting point for new projects
and as a reference for how to build a large scale fullstack Litestar application.

You can take pieces as needed, or use the entire thing as a starting point for your project.
It includes the following capabilities out of the box:

.. seealso:: It is built on the `Litestar <https://litestar.dev>`_, ReactJS, `Vite <https://vitejs.dev/>`_,
  :doc:`SAQ <saq:index>`, `TailwindCSS <https://tailwindcss.com/>`_ and comes with great features to reference:

  - User creation, authentication, and authorization via `UserController` and `AccessController`
  - Endpoints for listing, creating, updating, and deleting users
  - Login, logout, and signup functionalities with OAuth2 support
  - Profile management for authenticated users
  - Role-based access control using `RoleService` and guards
  - Job/Task Queues via :doc:`SAQ <saq:index>`
  - Fully featured frontend stack with ReactJS (supports Vue, Angular, and all other JS frameworks) and native Vite integration via
    the `litestar-vite <https://github.com/cofin/litestar-vite>`_ plugin
  - Fully featured backend API with Litestar
    - Includes the utilization of :doc:`Guards <litestar:usage/security/guards>` and team-based authentication,
    - Extensive CLI
  - Advanced logging with :doc:`structlog <structlog:index>`
  - SQLAlchemy ORMs, including the :doc:`Advanced Alchemy <advanced-alchemy:index>` helper library by `Jolt <https://jolt.rs>`_
    - UUIDv7 based Primary Keys using `uuid-utils`
  - AioSQL for raw queries without the ORM
  - Alembic migrations
  - Dockerized development and production environments
  - Test suite

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
