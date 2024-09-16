===========
Task Queues
===========

This application features a Redis-backed job/task queue thanks to the :doc:`SAQ <saq:index>` library.
You can use it to run one-off tasks, or recurring tasks on a cron-like schedule.

We are utilizing the `litestar-saq <https://github.com/cofin/litestar-saq>`_ plugin for native
integration with Litestar.

Background
----------

Your application's task queue serves a variety of purposes, this section aims to explain when and why you would
want to use a task queue.

Cron jobs are essential for updating the database, performing regular cleanup, sending scheduled emails for various
purposes, and conducting auditing or alerting activities.

Startup jobs focus on initializing essential services, loading initial data, conducting health checks, starting
monitoring services, and allocating necessary resources like database connections.

Conversely, shutdown jobs ensure the graceful release of resources, synchronization of
data with storage, completion of background jobs, and logging of shutdown activities.

Additionally, one-off jobs handle on-demand processing of user-generated content, execution of ad-hoc database tasks,
administrative operations like account resets or data migrations, and event-driven tasks triggered by
specific user actions or system events.

.. tip:: There are several alternatives to ``SAQ``, but we have chosen it for its speed, ease of use, and feature set.
  Some other options include:

  * Cron jobs via the OS
  * `Systemd timers <https://wiki.archlinux.org/title/systemd/Timers>`_
  * `RQ <https://github.com/rq/rq>`_
  * `ARQ <https://github.com/samuelcolvin/arq>`_
  * `SAQ <https://github.com/tobymao/saq>`_
  * `Celery <https://docs.celeryq.dev/en/stable/>`_

How
---

Jobs are set up on a per-domain basis. The ``Worker`` class is instantiated when the application starts up.
This calls :func:`litetar_saq.cli.run_worker_process` that has looks at certain directories to find jobs.

Each domain has a directory in it for jobs, in the pattern of ``src/app/domain/$DOMAIN/jobs``. There are separate
modules for each type of job (``scheduled``, ``startup``, ``shutdown``, and ``tasks``).

It is self-explanatory, jobs in the ``startup`` directory are run on startup, etc.
Scheduled jobs are the only slightly unique ones, in that they are a list of :class:`CronJob <saq.job.CronJob>`'s.
That looks something like:

.. code-block:: python

    scheduled_tasks: list[CronJob] = [
        CronJob(
            function=generate_analytics_report,
            cron="*/30 * * * *",
            heartbeat=30,
            unique=True,
            timeout=120,
        ),
        CronJob(
            function=send_daily_digest,
            cron="*/35 * * * *",
            heartbeat=30,
            unique=True,
            timeout=120,
        ),
    ]

So you see we have to scheduled jobs every 30 and 35 minutes. When the app starts up, these will run just as a
system cron job would.
