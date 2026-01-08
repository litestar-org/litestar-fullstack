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
| Meta      |     | [![Litestar Project](https://img.shields.io/badge/Litestar%20Org-%E2%AD%90%20Litestar-202235.svg?logo=python&labelColor=202235&color=edb641&logoColor=edb641)](https://github.com/litestar-org/litestar) [![types - Mypy](https://img.shields.io/badge/types-Mypy-202235.svg?logo=python&labelColor=202235&color=edb641&logoColor=edb641)](https://github.com/python/mypy) [![License - MIT](https://img.shields.io/badge/license-MIT-202235.svg?logo=python&labelColor=202235&color=edb641&logoColor=edb641)](https://spdx.org/licenses/) [![Litestar Sponsors](https://img.shields.io/badge/Sponsor-%E2%9D%A4-%23edb641.svg?&logo=github&logoColor=edb641&labelColor=202235)](https://github.com/sponsors/litestar-org) [![linting - Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json&labelColor=202235)](https://github.com/astral-sh/ruff) [![code style - Black](https://img.shields.io/badge/code%20style-black-000000.svg?logo=python&labelColor=202235&logoColor=edb641)](https://github.com/psf/black) [![All Contributors](https://img.shields.io/github/all-contributors/litestar-org/litestar?labelColor=202235&color=edb641&logoColor=edb641)](#contributors-) |

<!-- prettier-ignore-end -->
</div>

# Litestar Fullstack Reference Application

This is a reference application that you can use to get your next Litestar application running quickly.

It contains most of the boilerplate required for a production web API with features like:

- Latest Litestar configured with best practices
- Integration with [SQLAlchemy 2.0](https://www.sqlalchemy.org/), [SAQ (Simple Asynchronous Queue)](https://saq-py.readthedocs.io/en/latest/), [Structlog](https://www.structlog.org/en/stable/), and [Granian](https://github.com/emmett-framework/granian)
- Frontend integrated with Vite in SPA mode and React Email templates compiled to static HTML
- JWT auth with refresh tokens, MFA, OAuth, and admin surfaces
- Multi-stage Docker build using a minimal Python 3.13 runtime image (including a distroless variant)
- Team and role management with service/repository patterns and Advanced Alchemy filters

Take what you need and adapt it to your own projects

## Quick Start

To quickly get a development environment running, run the following:

```shell
make install
. .venv/bin/activate
```

### Local Development

```bash
cp .env.local.example .env
. .venv/bin/activate
make start-infra
app database upgrade
app run
```

### Docker

If you want to run the entire development environment containerized, you can run the following:

```bash
docker compose up
```
