==============
Object storage
==============

The template stores user-uploaded files (currently profile avatars) in
S3-compatible object storage rather than in the database or on the local disk.
This keeps the application stateless and lets the same code run unchanged
against a local container in development and a managed bucket in production.

How it works
^^^^^^^^^^^^

File handling is built on `advanced-alchemy`'s ``FileObject`` / ``StoredObject``
types, backed by `obstore`'s ``S3Store``:

- The ``User.avatar`` column is a ``StoredObject`` (stored as JSONB). It holds
  the object key, content type and size — never the bytes themselves.
- ``User.avatar_url`` is a hybrid property that returns ``/api/me/avatar`` when
  an avatar is set, so the API response schema stays stable.
- A single storage backend is registered once at application start by
  ``register_storage_backend()`` (see ``app/server/plugins.py``) and looked up by
  ``StorageSettings.BACKEND_KEY`` (``"s3"``). Registration is idempotent, so the
  test suite can install an in-memory store first and the production
  registration becomes a no-op.

Configuration
^^^^^^^^^^^^^

All settings are read from the environment by ``StorageSettings``
(``app/lib/settings.py``). The defaults target the bundled rustfs container, so
local development works with no configuration.

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Environment variable
     - Description
     - Default
   * - ``STORAGE_S3_ENDPOINT``
     - S3-compatible endpoint URL
     - ``http://localhost:19000``
   * - ``STORAGE_S3_ACCESS_KEY``
     - Access key ID
     - ``app``
   * - ``STORAGE_S3_SECRET_KEY``
     - Secret access key
     - ``app``
   * - ``STORAGE_S3_BUCKET``
     - Bucket name
     - ``uploads``
   * - ``STORAGE_S3_REGION``
     - Region
     - ``us-east-1``
   * - ``STORAGE_S3_ALLOW_HTTP``
     - Allow plain-HTTP connections (needed for local rustfs)
     - ``true``

Local development
^^^^^^^^^^^^^^^^^

The infrastructure compose file ships a `rustfs <https://rustfs.com>`_ service —
a lightweight, Rust-based, S3-compatible store — so no MinIO or AWS account is
needed locally:

.. code-block:: bash

    docker compose -f tools/deploy/docker/docker-compose.infra.yml up -d

This exposes:

- **S3 API** on ``http://localhost:19000`` (used by the app)
- **Web console** on ``http://localhost:19001`` (browse uploaded objects)

The default credentials are ``app`` / ``app`` and the default bucket is
``uploads``. These match the ``StorageSettings`` defaults, so nothing else is
required for avatars to work end to end.

Using the avatar endpoints
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The current user's avatar is managed through three authenticated endpoints on
``ProfileController``:

.. list-table::
   :header-rows: 1
   :widths: 20 25 55

   * - Method
     - Path
     - Behaviour
   * - ``POST``
     - ``/api/me/avatar``
     - Multipart upload (field ``file``). Replaces any existing avatar.
   * - ``GET``
     - ``/api/me/avatar``
     - Streams the stored image bytes with the detected content type.
   * - ``DELETE``
     - ``/api/me/avatar``
     - Removes the avatar (``204 No Content``).

The server is the security boundary: the stored content type is derived from
**magic-byte sniffing** of the upload (not the client ``Content-Type`` header),
the object key is generated server-side as ``avatars/{user_id}/{uuid4}.{ext}``
(so the client filename can never cause path traversal), and the request body is
capped at 5 MB by ``request_max_body_size`` so oversize uploads are rejected
before buffering. Replacing or deleting an avatar cleans up the previous object
automatically via advanced-alchemy's session tracker.

The single-page app wires these into the profile page (**Profile settings →
Profile picture**), with the avatar also shown in the sidebar user menu. Because
the avatar lives at a stable URL, the frontend appends a cache-busting version
query parameter so a replaced image refreshes immediately.

Production deployment
^^^^^^^^^^^^^^^^^^^^^

To run against a managed bucket (for example AWS S3), point the application at
your bucket and disable plain HTTP:

.. code-block:: bash

    STORAGE_S3_ENDPOINT=https://s3.us-east-1.amazonaws.com
    STORAGE_S3_ACCESS_KEY=...
    STORAGE_S3_SECRET_KEY=...
    STORAGE_S3_BUCKET=your-bucket
    STORAGE_S3_REGION=us-east-1
    STORAGE_S3_ALLOW_HTTP=false

Any S3-compatible provider works the same way (Cloudflare R2, Backblaze B2,
DigitalOcean Spaces, MinIO) — set ``STORAGE_S3_ENDPOINT`` to the provider's
endpoint.

.. note::
   For a non-S3 backend such as Google Cloud Storage, swap the ``S3Store`` in
   ``register_storage_backend()`` for the corresponding `obstore` store (e.g.
   ``GCSStore``) and supply its credentials. The rest of the application is
   storage-agnostic because it only depends on the registered backend key.
