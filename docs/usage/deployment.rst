==========
Deployment
==========

.. note:: This section is a work in progress.
  Would you like to contribute? See the :doc:`/contribution-guide`.

No matter how you decide to deploy your application, this is a Litestar app and the
:doc:`Litestar Deployment Guide <litestar:topics/deployment/index>` is a great place to start.

Docker
------

This repository contains example ``Dockerfile``'s and ``docker-compose.yml``'s for deploying
your application for development and production.

Development
^^^^^^^^^^^

Everyone's development environment is different, but we've included a ``docker-compose.infra.yml`` file that
contains the required infrastructure services for running the application.
This includes a PostgreSQL database, a Redis cache, local mail with `MailHog <https://github.com/mailhog/MailHog>`_,
and object storage with `Minio <https://min.io/>`_.

This allows you to just `docker compose up` to start your services, and then run the application
locally with (for example) the Litestar CLI: ``litestar run --debug --reload``.

We also have a ``Dockerfile`` for development:

.. dropdown:: Example ``Dockerfile`` for development

  .. literalinclude:: ../../deploy/docker/dev/Dockerfile
     :language: dockerfile
     :linenos:

Production
^^^^^^^^^^

.. dropdown:: Example ``Dockerfile`` for production

  .. literalinclude:: ../../deploy/docker/run/Dockerfile
     :language: dockerfile
     :linenos:

For Docker Compose, run the ``docker-compose.yml`` file, replacing the environment
variables as needed with your own values.

Railway
-------

This repository also has a template on `Railway <https://railway.app/template/KmHMvQ?referralCode=BMcs0x>`_.

.. note:: This link is a referral link that will give us a credit if you decide to utilize the service
  and host your application(s) on their platform. This helps us to continue to provide great open source
  software for the community by offsetting our hosting costs, and doesn't cost you anything extra.

Cloud Platforms
---------------

.. todo:: Add examples for deploying to cloud platforms.
  Would you like to contribute? See the :doc:`/contribution-guide`.


Service
-------

You can also wrap this application into a ``systemd`` service, or use a process manager like
`Supervisor <http://supervisord.org/>`_.

.. dropdown:: Example ``systemd`` service

  .. literalinclude:: ../examples/app.service
     :language: ini
     :linenos:

.. dropdown:: Manage the ``systemd`` service

    .. code-block:: bash

        # Enable the service.
        sudo systemctl enable app

        # Stop the service.
        sudo systemctl stop app

        # (Re)start the service.
        sudo systemctl restart app
