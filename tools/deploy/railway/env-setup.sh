#!/usr/bin/env bash
# Railway environment variable helper (email, GitHub OAuth, .env file import).
#
# Usage:
#   ./env-setup.sh --email
#   ./env-setup.sh --github-oauth
#   ./env-setup.sh --from-file .env.railway
#   ./env-setup.sh --set KEY=VALUE

set -euo pipefail

APP_SERVICE_NAME="${APP_SERVICE_NAME:-Litestar Web Frontend}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

CONFIGURE_EMAIL=false
CONFIGURE_GITHUB_OAUTH=false
ENV_FILE=""
SET_VAR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --email) CONFIGURE_EMAIL=true; shift ;;
        --github-oauth) CONFIGURE_GITHUB_OAUTH=true; shift ;;
        --from-file) ENV_FILE="$2"; shift 2 ;;
        --set) SET_VAR="$2"; shift 2 ;;
        *)
            echo "Usage: ./env-setup.sh [--email] [--github-oauth] [--from-file .env] [--set KEY=VALUE]"
            exit 1
            ;;
    esac
done

log_info() { echo -e "\033[0;34m[INFO]\033[0m $1"; }
log_ok() { echo -e "\033[0;32m[OK]\033[0m $1"; }
log_err() { echo -e "\033[0;31m[ERROR]\033[0m $1" >&2; }

preflight() {
    command -v railway &> /dev/null || { log_err "Railway CLI not installed."; exit 1; }
    railway whoami &> /dev/null || { log_err "Run 'railway login' first."; exit 1; }
    cd "${PROJECT_ROOT}"
    railway status &> /dev/null || { log_err "No Railway project linked. Run ./deploy.sh first."; exit 1; }
}

load_from_file() {
    [[ -f "${ENV_FILE}" ]] || { log_err "File not found: ${ENV_FILE}"; exit 1; }
    local pairs=()
    while IFS='=' read -r key value || [[ -n "$key" ]]; do
        [[ -z "$key" || "$key" =~ ^# ]] && continue
        value="${value%\"}"; value="${value#\"}"
        value="${value%\'}"; value="${value#\'}"
        [[ -z "$value" || "$value" == "your-"* ]] && continue
        pairs+=("${key}=${value}")
    done < "${ENV_FILE}"
    if [[ "${#pairs[@]}" -gt 0 ]]; then
        railway variable set --service "${APP_SERVICE_NAME}" --skip-deploys "${pairs[@]}"
    fi
    log_ok "Loaded ${#pairs[@]} variables from ${ENV_FILE}"
}

configure_email() {
    read -r -p "Resend API key: " resend_key
    read -r -p "Verified 'From' email: " from_addr
    read -r -p "'From' display name [Litestar Fullstack SPA]: " from_name
    from_name="${from_name:-Litestar Fullstack SPA}"

    railway variable set --service "${APP_SERVICE_NAME}" \
        "EMAIL_BACKEND=resend" \
        "EMAIL_FROM_ADDRESS=${from_addr}" \
        "EMAIL_FROM_NAME=${from_name}" \
        "RESEND_API_KEY=${resend_key}"
    log_ok "Configured Resend email on ${APP_SERVICE_NAME}"
}

configure_github_oauth() {
    local app_url
    app_url="$(railway variable list --service "${APP_SERVICE_NAME}" --kv 2>/dev/null | grep '^APP_URL=' | head -1 | cut -d'=' -f2- || true)"
    if [[ -z "${app_url}" ]] || [[ "${app_url}" == *'${{'* ]]; then
        app_url="$(railway domain --json 2>/dev/null | grep -o 'https://[^"]*' | head -1 || true)"
    fi
    if [[ -n "${app_url}" ]]; then
        log_info "GitHub OAuth Callback URL: ${app_url%/}/api/auth/oauth/github/callback"
    fi

    local client_id="${GITHUB_OAUTH2_CLIENT_ID:-}"
    local client_secret="${GITHUB_OAUTH2_CLIENT_SECRET:-}"
    if [[ -z "${client_id}" ]]; then
        read -r -p "GitHub OAuth Client ID: " client_id
    fi
    if [[ -z "${client_secret}" ]]; then
        read -r -s -p "GitHub OAuth Client Secret: " client_secret
        echo ""
    fi
    [[ -n "${client_id}" && -n "${client_secret}" ]] || { log_err "Client ID and Secret are required."; exit 1; }

    railway variable set --service "${APP_SERVICE_NAME}" \
        "GITHUB_OAUTH2_CLIENT_ID=${client_id}" \
        "GITHUB_OAUTH2_CLIENT_SECRET=${client_secret}"
    log_ok "Configured GitHub OAuth on ${APP_SERVICE_NAME}"
}

main() {
    preflight
    if [[ -n "${ENV_FILE}" ]]; then
        load_from_file
    elif [[ -n "${SET_VAR}" ]]; then
        railway variable set --service "${APP_SERVICE_NAME}" "${SET_VAR}"
        log_ok "Updated ${SET_VAR%%=*}"
    elif [[ "${CONFIGURE_EMAIL}" = true ]]; then
        configure_email
    elif [[ "${CONFIGURE_GITHUB_OAUTH}" = true ]]; then
        configure_github_oauth
    else
        echo "1) List variables  2) Configure Resend email  3) Configure GitHub OAuth  4) Exit"
        read -r -p "Choice [1-4]: " choice
        case "${choice}" in
            1) railway variable list --service "${APP_SERVICE_NAME}" ;;
            2) configure_email ;;
            3) configure_github_oauth ;;
            *) exit 0 ;;
        esac
    fi
}

main "$@"
