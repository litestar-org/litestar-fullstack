===
cli
===

Command line interface for the application.

Litestar CLI
------------

.. click:: litestar.cli:litestar_group
    :prog: app
    :nested: full

Database CLI
^^^^^^^^^^^^

.. click:: advanced_alchemy.extensions.litestar.cli:database_group
    :prog: app database
    :nested: full

User management CLI
^^^^^^^^^^^^^^^^^^^

.. click:: app.cli.commands:user_management_group
    :prog: app user
    :nested: full
