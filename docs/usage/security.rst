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
- **OAuth2 / OIDC**: Optional Google OIDC (with JWKS verification) and GitHub OAuth2 enabled via ``GOOGLE_OAUTH2_CLIENT_ID``/``SECRET`` and ``GITHUB_OAUTH2_CLIENT_ID``/``SECRET``, mounted under ``/api/auth/oauth/{provider}/...``.
- **Personal API Keys**: Self-service hashed keys under ``/api/me/api-keys`` support Bearer authentication, rotation, revocation, and scoped access to ``/mcp``.
- **Tenant & Role Guards**: Team routes enforce ``requires_team_role("member" | "admin" | "owner")`` and admin routes enforce ``requires_role("superuser")`` via ``AppAuthorizationResolver``.
