#!/usr/bin/env bash
# Idempotent Railway deployment script.
# Default topology: single app container (embedded ASGI queue worker) + PostgreSQL over private networking.
# Pass --dedicated-worker to provision an optional standalone queue worker service for horizontal scaling.
#
# Usage:
#   ./deploy.sh [--detach] [--skip-setup] [--dedicated-worker] [--email] [--github-oauth]

set -euo pipefail

DETACH=false
SKIP_SETUP=false
DEDICATED_WORKER=false
CONFIGURE_EMAIL=false
CONFIGURE_GITHUB_OAUTH=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

APP_SERVICE_NAME="${APP_SERVICE_NAME:-Litestar Web Frontend}"
WORKER_SERVICE_NAME="${WORKER_SERVICE_NAME:-Queue Worker}"

while [[ $# -gt 0 ]]; do
    case $1 in
        --detach) DETACH=true; shift ;;
        --skip-setup) SKIP_SETUP=true; shift ;;
        --dedicated-worker) DEDICATED_WORKER=true; shift ;;
        --email) CONFIGURE_EMAIL=true; shift ;;
        --github-oauth) CONFIGURE_GITHUB_OAUTH=true; shift ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./deploy.sh [--detach] [--skip-setup] [--dedicated-worker] [--email] [--github-oauth]"
            exit 1
            ;;
    esac
done

log_info() { echo -e "\033[0;34m[INFO]\033[0m $1"; }
log_ok() { echo -e "\033[0;32m[OK]\033[0m $1"; }
log_err() { echo -e "\033[0;31m[ERROR]\033[0m $1" >&2; }

ensure_cli_and_auth() {
    if ! command -v railway &> /dev/null; then
        log_err "Railway CLI not found. Install via: npm i -g @railway/cli"
        exit 1
    fi
    if ! railway whoami &> /dev/null; then
        railway login
    fi
    log_ok "Authenticated as $(railway whoami)"
}

ensure_project() {
    cd "${PROJECT_ROOT}"
    if railway status &> /dev/null; then
        log_ok "Using linked Railway project"
        return 0
    fi
    read -r -p "Enter project name [litestar-fullstack-spa]: " project_name
    project_name="${project_name:-litestar-fullstack-spa}"
    railway init --name "${project_name}"
    log_ok "Created project: ${project_name}"
}

ensure_service() {
    local name="$1"
    if railway status --json 2>/dev/null | grep -qi "\"${name}\""; then
        log_ok "Service exists: ${name}"
    else
        log_info "Creating service: ${name}"
        railway add --service "${name}"
    fi
}

ensure_database() {
    if railway status --json 2>/dev/null | grep -qi 'postgres'; then
        log_ok "PostgreSQL already provisioned"
        return 0
    fi
    log_info "Provisioning PostgreSQL..."
    railway add --database postgres
    log_ok "PostgreSQL provisioned"
}

configure_service_config() {
    local service="$1"
    local dockerfile="$2"
    local config_file="$3"
    railway environment edit --service-config "${service}" build.builder DOCKERFILE 2>/dev/null || true
    railway environment edit --service-config "${service}" build.dockerfilePath "${dockerfile}" 2>/dev/null || true
    railway environment edit --service-config "${service}" deploy.configFile "${config_file}" 2>/dev/null || true
}

configure_app_env() {
    local placement="asgi"
    if [ "${DEDICATED_WORKER}" = true ]; then
        placement="external"
    fi

    local existing
    existing="$(railway variable list --service "${APP_SERVICE_NAME}" --kv 2>/dev/null || true)"

    local args=(
        --service "${APP_SERVICE_NAME}"
        --skip-deploys
        "LITESTAR_DEBUG=false"
        "VITE_DEV_MODE=false"
        "COOKIE_SECURE=true"
        "LITESTAR_TRUSTED_PROXIES=*"
        "DATABASE_ECHO=false"
        "SQLALCHEMY_LOG_LEVEL=30"
        "QUEUES_PLACEMENT=${placement}"
        "QUEUES_TERMINAL_RETENTION_SECONDS=604800"
        'LITESTAR_PORT=${{PORT}}'
        'DATABASE_URL=${{Postgres.DATABASE_PRIVATE_URL}}'
        'APP_URL=https://${{RAILWAY_PUBLIC_DOMAIN}}'
    )

    if ! grep -q '^SECRET_KEY=' <<< "${existing}"; then
        local secret_key
        secret_key="$(openssl rand -base64 32 | tr -d '=' | tr '+/' '-_')"
        args+=("SECRET_KEY=${secret_key}" "EMAIL_BACKEND=console")
    fi

    railway variable set "${args[@]}"
    log_ok "Configured ${APP_SERVICE_NAME} (QUEUES_PLACEMENT=${placement}, private Postgres URL)"
}

configure_worker_env() {
    local secret_key
    secret_key="$(railway variable list --service "${APP_SERVICE_NAME}" --kv 2>/dev/null | grep '^SECRET_KEY=' | cut -d'=' -f2-)"
    railway variable set \
        --service "${WORKER_SERVICE_NAME}" \
        --skip-deploys \
        "SECRET_KEY=${secret_key}" \
        "LITESTAR_DEBUG=false" \
        "DATABASE_ECHO=false" \
        "SQLALCHEMY_LOG_LEVEL=30" \
        "QUEUES_PLACEMENT=external" \
        "QUEUES_TERMINAL_RETENTION_SECONDS=604800" \
        'DATABASE_URL=${{Postgres.DATABASE_PRIVATE_URL}}'
    log_ok "Configured ${WORKER_SERVICE_NAME}"
}

deploy_services() {
    cd "${PROJECT_ROOT}"
    local up_flags=(--detach -m "Deploy Litestar Fullstack SPA")
    if [ "${DETACH}" = false ]; then
        up_flags=(--ci -m "Deploy Litestar Fullstack SPA")
    fi

    log_info "Deploying ${APP_SERVICE_NAME}..."
    railway up --service "${APP_SERVICE_NAME}" "${up_flags[@]}"

    if [ "${DEDICATED_WORKER}" = true ]; then
        log_info "Deploying ${WORKER_SERVICE_NAME}..."
        railway up --service "${WORKER_SERVICE_NAME}" --detach -m "Deploy Queue Worker"
    fi
}

main() {
    ensure_cli_and_auth
    cd "${PROJECT_ROOT}"

    if [ "${SKIP_SETUP}" = false ]; then
        ensure_project
        ensure_database
        ensure_service "${APP_SERVICE_NAME}"
        railway service link "${APP_SERVICE_NAME}" 2>/dev/null || true
        if ! railway domain --json 2>/dev/null | grep -q 'railway.app'; then
            railway domain
        fi
        configure_service_config \
            "${APP_SERVICE_NAME}" \
            "tools/deploy/docker/Dockerfile.distroless" \
            "tools/deploy/railway/railway.app.json"
        configure_app_env

        if [ "${DEDICATED_WORKER}" = true ]; then
            ensure_service "${WORKER_SERVICE_NAME}"
            configure_service_config \
                "${WORKER_SERVICE_NAME}" \
                "tools/deploy/docker/Dockerfile.worker" \
                "tools/deploy/railway/railway.worker.json"
            configure_worker_env
        fi
    fi

    deploy_services

    if [ "${CONFIGURE_EMAIL}" = true ]; then
        "${SCRIPT_DIR}/env-setup.sh" --email
    fi
    if [ "${CONFIGURE_GITHUB_OAUTH}" = true ]; then
        "${SCRIPT_DIR}/env-setup.sh" --github-oauth
    fi

    log_ok "Railway deployment complete (single-service ASGI worker=$([ "${DEDICATED_WORKER}" = true ] && echo 'false' || echo 'true'))"
}

main "$@"
