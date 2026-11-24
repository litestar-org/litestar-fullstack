===============
Getting Started
===============

Bootstrap Python (``uv``) and frontend/email (``bun``) dependencies with:

.. code-block:: bash

    make install

This creates ``.venv`` via ``uv`` and installs packages in ``src/js/web`` and ``src/js/templates``.

Configure ``.env``
------------------

Copy the sample environment file:

.. code-block:: bash

    cp .env.local.example .env

Generate a 32-byte ``SECRET_KEY`` for HKDF subkey derivation (sessions, CSRF, MFA, OAuth, API keys):

.. code-block:: bash

    openssl rand -base64 32

Start Infrastructure & Run Migrations
-------------------------------------

Start PostgreSQL, Mailpit, and RustFS, build email templates, and run Alembic migrations:

.. code-block:: bash

    make start-infra
    make build-emails
    uv run app database upgrade
