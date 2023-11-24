===============
Getting Started
===============

The following is a guide to help you get this repository running.

Setup
-----

Most of the development-related tasks are included in the ``Makefile`` (See: :doc:`development`).
To install an environment, with all development packages run:

.. code-block:: bash

    make install

This command does the following:

- Install ``pdm`` if it is not available in the path.
- Create a virtual environment with all dependencies configured
- Build assets to be hosted by production asset server

Edit ``.env`` configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^

There is a sample ``.env`` file located in the root of the repository.

.. code-block:: bash

    cp .env.example .env

.. tip:: ``SECRET_KEY``, ``DATABASE_URI``, and ``REDIS_URL`` are the most important config settings.
  Be sure to set this properly.

You can generate a ``SECRET_KEY`` by running:

.. code-block:: bash

    ❯ openssl rand -base64 32

    +U9UcN0meCsxkShMINkqZ7pcwpEpOC9AwOArZI6mYDU=

Deploy Database Migrations
^^^^^^^^^^^^^^^^^^^^^^^^^^

You can run most of the database commands with the integrated CLI tool.

To deploy migration to the database, execute:

.. code-block:: bash

    ❯ app database upgrade
    2023-06-16T16:55:17.048183Z [info     ] Context impl PostgresqlImpl.
    2023-06-16T16:55:17.048251Z [info     ] Will assume transactional DDL.
