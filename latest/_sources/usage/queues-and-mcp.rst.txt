=============================
Queues, AsyncAPI & MCP Server
=============================

PostgreSQL Background Queues
----------------------------

Background jobs use ``litestar-queues`` backed by PostgreSQL (``SQLAlchemyBackendConfig`` with
``worker_wakeups=True`` for ``LISTEN``/``NOTIFY``). Tasks are discovered automatically via
``AutowirePlugin(integrations=["queues"])`` across four queues: ``default``, ``emails``,
``reports``, and ``maintenance``.

- Run a dedicated worker: ``uv run app queues run``
- Inspect worker status: ``uv run app queues status``
- Execute scheduled maintenance (stale task recovery, retention, schedule assertions):

  .. code-block:: bash

      uv run app queues run-maintenance --json

Realtime Queue Events (AsyncAPI)
--------------------------------

``QueueEventsConfig`` publishes task lifecycle and progress events on ``/api/queues/events`` over
SSE and WebSocket, gated by authentication and per-task/superuser channel authorization.
``AsyncAPIPlugin`` exposes the AsyncAPI document at ``/asyncapi/asyncapi.json``, and
``litestar-vite`` generates typed frontend channel helpers under ``src/js/web/src/lib/generated``.

Model Context Protocol (MCP)
----------------------------

``LitestarMCP`` mounts a JSON-RPC server at ``/mcp`` protected by ``required("api-key")`` with
redacted audit hooks writing to ``audit_log``. Only curated user-scoped resources
(``system_health``, ``user_profile``, ``teams_list``, ``tags_catalog``, ``app://teams/{team_id}``)
and safe tools (``create_tag``, ``list_my_tasks``, ``enqueue_team_report``) are exposed; admin and
destructive routes are excluded.

Validate tool description bounds in CI or locally:

.. code-block:: bash

    uv run app mcp export-tool-spec --strict-bounds
