=========================
Security & Authentication
=========================

Authentication and authorization are assembled declaratively by ``litestar-security`` in
``app.domain.accounts.security.config.build_security_config``.

Key Capabilities
----------------

- **Fail-Closed Controllers**: Protected routes subclass ``SecureController``; public routes explicitly subclass ``PublicController`` or opt in via ``@public``. Audit every route with:

  .. code-block:: bash

      uv run app security routes

- **Cookie Sessions & CSRF**: ``LocalAuth.session`` stores server-side sessions in PostgreSQL via ``SQLAlchemyStore`` on ``app_store`` with ``HttpOnly``, ``SameSite=Lax`` cookies and HKDF-derived CSRF tokens (``XSRF-TOKEN`` / ``X-XSRF-TOKEN``).
- **Step-Up TOTP MFA**: Encrypted TOTP secrets (``AESGCMSecretProtector``) and peppered recovery codes enforce ``require_at_login="enrolled"`` with single-use login challenges and step-up grants (``totp-enroll``, ``totp-remove``, ``recovery-codes``).
- **WebAuthn Passkeys**: Credential registration and assertion verification are stored in ``auth_passkey`` and ``auth_passkey_challenge``.
- **OAuth2**: Optional GitHub OAuth2 enabled via ``GITHUB_OAUTH2_CLIENT_ID`` / ``GITHUB_OAUTH2_CLIENT_SECRET``, mounted under ``/api/auth/oauth/github/...``. The callback must be served over HTTPS, so ``APP_URL`` needs an ``https://`` origin whenever GitHub sign-in is enabled.
- **Personal API Keys**: Self-service hashed keys under ``/api/me/api-keys`` support Bearer authentication, rotation, revocation, and scoped access to ``/mcp``.
- **Password Confirmation**: Creating, rotating, or revoking an API key, changing the password, and deleting the account are admitted within five minutes of sign-in. After that the request must carry ``currentPassword``; without it the API answers ``403`` with ``code`` set to ``reauthentication_required`` and the SPA prompts for the password and retries.
- **Application Access**: Every account is created with the ``Application Access`` role, which is required to use the application. A signed-in user who holds neither that role nor ``Superuser`` gets ``403`` with ``code`` set to ``application_access_required`` on every route except sign-out.
- **Error Responses**: Errors are ``application/problem+json`` with ``status``, ``title`` (the HTTP reason phrase), ``detail`` (the human-readable message), and, where relevant, a machine-readable ``code``.
- **Email Verification**: ``REGISTRATION_REQUIRE_VERIFICATION`` (default ``true``) decides whether new password accounts must confirm their email address before signing in.
- **Tenant & Role Guards**: Team routes enforce ``requires_team_role("member" | "admin" | "owner")`` and admin routes enforce ``requires_role("superuser")`` via ``AppAuthorizationResolver``.
