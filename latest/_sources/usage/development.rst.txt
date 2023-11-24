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

- ``pdm upgrade``
- ``npm update``
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

This command is a shorthand for executing ``app database make-migrations``.

.. code-block:: shell

    make migrations

Upgrade a Database to the Latest Revision
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This command is a shorthand for executing ``app database upgrade``.

.. code-block:: shell

    make migrate

Execute Full Test Suite
^^^^^^^^^^^^^^^^^^^^^^^

This command executes all tests for the project.

.. code-block:: shell

    make test

Full Makefile
-------------

.. dropdown:: Full Makefile

    .. literalinclude:: ../../Makefile
        :language: make
