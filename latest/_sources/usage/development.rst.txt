===========
Development
===========

This section describes tips on developing using this example repository.

Makefile
--------

This repository includes a ``Makefile`` with common commands for development.


Install Development Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This command will remove any existing environment and install a new environment with the latest dependencies.

.. code-block:: shell

    make install

Upgrade Project Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This command will upgrade all components of the application at the same time. It automatically executes:

- ``uv lock --upgrade``
- ``bun update``
- ``pre-commit autoupdate``

.. code-block:: shell

    make upgrade

Execute Pre-commit
^^^^^^^^^^^^^^^^^^

This command will automatically execute the pre-commit process for the project.

.. code-block:: shell

    make lint

Generate New Migrations
^^^^^^^^^^^^^^^^^^^^^^^

Create a new migration with the Litestar CLI:

.. code-block:: shell

    uv run app database make-migrations

Upgrade a Database to the Latest Revision
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Upgrade the database to the latest revision:

.. code-block:: shell

    uv run app database upgrade

Execute Full Test Suite
^^^^^^^^^^^^^^^^^^^^^^^

This command executes all tests for the project.

.. code-block:: shell

    make test

Generate TypeScript Types
^^^^^^^^^^^^^^^^^^^^^^^^^

After backend schema changes, regenerate the TypeScript client:

.. code-block:: shell

    make types

Full Makefile
-------------

.. dropdown:: Full Makefile

    .. literalinclude:: ../../Makefile
        :language: make
