<!-- markdownlint-disable -->
<p align="center">
  <img src="https://raw.githubusercontent.com/litestar-org/branding/1dc4635b192d29d864fcee6f3f73ea0ff6fecf10/assets/Branding%20-%20SVG%20-%20Transparent/Fullstack%20-%20Banner%20-%20Inline%20-%20Light.svg#gh-light-mode-only" alt="Litestar Logo - Light" width="100%" height="auto" />
  <img src="https://raw.githubusercontent.com/litestar-org/branding/1dc4635b192d29d864fcee6f3f73ea0ff6fecf10/assets/Branding%20-%20SVG%20-%20Transparent/Fullstack%20-%20Banner%20-%20Inline%20-%20Dark.svg#gh-dark-mode-only" alt="Litestar Logo - Dark" width="100%" height="auto" />
</p>
<!-- markdownlint-restore -->

<div align="center">
<!-- prettier-ignore-start -->

| Project   |     | Status                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| --------- | :-- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CI/CD     |     | [![Tests and Linting](https://github.com/litestar-org/litestar-fullstack/actions/workflows/ci.yaml/badge.svg)](https://github.com/litestar-org/litestar-fullstack/actions/workflows/ci.yaml)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Quality   |     | [![Coverage](https://sonarcloud.io/api/project_badges/measure?project=litestar-org_litestar-fullstack&metric=coverage)](https://sonarcloud.io/summary/new_code?id=litestar-org_litestar) [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=litestar-org_litestar-fullstack&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=litestar-org_litestar) [![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=litestar-org_litestar-fullstack&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=litestar-org_litestar) [![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=litestar-org_litestar-fullstack&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=litestar-org_litestar) [![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=litestar-org_litestar-fullstack&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=litestar-org_litestar)                                                                                                                                                                                                                     |
| Community |     | [![Reddit](https://img.shields.io/reddit/subreddit-subscribers/litestarapi?label=r%2FLitestar&logo=reddit&labelColor=202235&color=edb641&logoColor=edb641)](https://reddit.com/r/litestarapi) [![Discord](https://img.shields.io/discord/919193495116337154?labelColor=202235&color=edb641&label=chat%20on%20discord&logo=discord&logoColor=edb641)](https://discord.gg/litestar) [![Matrix](https://img.shields.io/badge/chat%20on%20Matrix-bridged-202235?labelColor=202235&color=edb641&logo=matrix&logoColor=edb641)](https://matrix.to/#/#litestar:matrix.org) [![Medium](https://img.shields.io/badge/Medium-202235?labelColor=202235&color=edb641&logo=medium&logoColor=edb641)](https://blog.litestar.dev) [![Twitter](https://img.shields.io/twitter/follow/LitestarAPI?labelColor=202235&color=edb641&logo=twitter&logoColor=edb641&style=flat)](https://twitter.com/LitestarAPI) [![Blog](https://img.shields.io/badge/Blog-litestar.dev-202235?logo=blogger&labelColor=202235&color=edb641&logoColor=edb641)](https://blog.litestar.dev)                                                                                                                                                                                                |
| Meta      |     | [![Litestar Project](https://img.shields.io/badge/Litestar%20Org-%E2%AD%90%20Litestar-202235.svg?logo=python&labelColor=202235&color=edb641&logoColor=edb641)](https://github.com/litestar-org/litestar) [![types - Mypy](https://img.shields.io/badge/types-Mypy-202235.svg?logo=python&labelColor=202235&color=edb641&logoColor=edb641)](https://github.com/python/mypy) [![License - MIT](https://img.shields.io/badge/license-MIT-202235.svg?logo=python&labelColor=202235&color=edb641&logoColor=edb641)](https://spdx.org/licenses/) [![Litestar Sponsors](https://img.shields.io/badge/Sponsor-%E2%9D%A4-%23edb641.svg?&logo=github&logoColor=edb641&labelColor=202235)](https://github.com/sponsors/litestar-org) [![linting - Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json&labelColor=202235)](https://github.com/astral-sh/ruff) [![All Contributors](https://img.shields.io/github/all-contributors/litestar-org/litestar?labelColor=202235&color=edb641&logoColor=edb641)](#contributors-) |

<!-- prettier-ignore-end -->
</div>

# Litestar Fullstack Reference Application

Production-ready fullstack reference application built on the first-party Litestar ecosystem, packaged with `uv_build` and backed solely by PostgreSQL (`asyncpg`) with no external cache or broker dependency.

## Stack Highlights

- **Web & Runtime**: [Litestar](https://docs.litestar.dev/) + [Granian](https://github.com/emmett-framework/granian) (`litestar-granian`), `StructlogPlugin`, `ProblemDetailsPlugin`, and `litestar-autowire` for zero-boilerplate domain discovery.
- **Database**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) + [Advanced Alchemy](https://docs.advanced-alchemy.litestar.dev/) with `asyncpg`, `UUIDv7AuditBase`, typed `FilterSet` query dependencies, `ServiceGroup`, and `SQLAlchemyStore`.
- **Security & Auth**: `litestar-security` with fail-closed `SecureController`, `HttpOnly` cookie-backed `LocalAuth.session` + CSRF, step-up TOTP MFA with recovery codes, WebAuthn Passkeys, Google OIDC / GitHub OAuth2, personal API keys, and `app security routes` auditing.
- **Background Queues & Realtime**: PostgreSQL-backed `litestar-queues` (`SQLAlchemyBackendConfig(worker_wakeups=True)` with `LISTEN`/`NOTIFY`), `QueuedBackgroundTask`, scheduled maintenance (`app queues run-maintenance --json`), and `litestar-asyncapi` + SSE/WebSocket live event streaming.
- **MCP Server**: `litestar-mcp` mounted at `/mcp` with API-key authentication, strict tool description bounds (`app mcp export-tool-spec --strict-bounds`), and redacted audit logging.
- **Frontend & Emails**: React 19 SPA with TanStack Router/Query/Table, Tailwind CSS v4, Radix UI, generated OpenAPI TypeScript client + AsyncAPI channel helpers (`litestar-vite`), and React Email templates compiled to static HTML (`litestar-email`).
- **Deployment**: Postgres-only multi-stage Docker (including distroless and standalone worker images), Railway, and Kubernetes blueprints.

## Quick Start

```shell
make install
cp .env.local.example .env
```

### Local Development

Start PostgreSQL, Mailpit, and RustFS via Docker Compose, apply migrations, build email templates, and launch the API + Vite dev server:

```bash
make start-infra
make build-emails
uv run app database upgrade
uv run app run
```

Run a standalone queue worker when using `QUEUES_PLACEMENT=external`:

```bash
uv run app queues run
```

### Common Commands

| Command | Purpose |
| --- | --- |
| `make install` | Bootstrap Python (`uv`) and frontend/email (`bun`) dependencies |
| `make types` | Export OpenAPI & AsyncAPI schemas and regenerate the TypeScript SDK |
| `make build-emails` | Compile React Email templates to static HTML in `src/py/app/server/static/email` |
| `make frontend-check` | Run Biome lint checks and Vitest tests under `src/js/web` |
| `make test` | Run pytest suite with PostgreSQL template database cloning |
| `make build-wheel` | Build emails, frontend SPA bundle, and `uv_build` wheel in `dist/` |
| `make docs` | Build Sphinx documentation strictly (`-W --keep-going`) |

### Docker

Run the full stack (PostgreSQL, migrator, Granian API, and standalone queue worker):

```bash
docker compose up
```
