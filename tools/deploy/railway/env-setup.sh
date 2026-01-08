#!/usr/bin/env bash
# =============================================================================
# Railway Environment Configuration Script
# =============================================================================
# Helper script for configuring optional environment variables.
# For initial setup, use ./deploy.sh instead.
#
# Usage:
#   ./env-setup.sh                    # Interactive menu
#   ./env-setup.sh --email            # Configure Resend email
#   ./env-setup.sh --github-oauth     # Configure GitHub OAuth
#   ./env-setup.sh --from-file .env   # Load variables from file
#   ./env-setup.sh --set KEY=VALUE    # Set a single variable
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
CONFIGURE_EMAIL=false
CONFIGURE_GITHUB_OAUTH=false
ENV_FILE=""
SET_VAR=""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# -----------------------------------------------------------------------------
# Parse Arguments
# -----------------------------------------------------------------------------

while [[ $# -gt 0 ]]; do
    case $1 in
        --email)
            CONFIGURE_EMAIL=true
            shift
            ;;
        --github-oauth)
            CONFIGURE_GITHUB_OAUTH=true
            shift
            ;;
        --from-file)
            ENV_FILE="$2"
            shift 2
            ;;
        --set)
            SET_VAR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./env-setup.sh [--email] [--github-oauth] [--from-file .env] [--set KEY=VALUE]"
            exit 1
            ;;
    esac
done

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

get_app_url() {
    local app_url=""
    app_url=$(railway variables --kv 2>/dev/null | grep -E '^APP_URL=' | head -1 | cut -d'=' -f2- || true)
    if [ -z "${app_url}" ]; then
        app_url=$(railway status --json 2>/dev/null | grep -o '"url": *"[^"]*"' | head -1 | cut -d'"' -f4 || true)
    fi
    echo "${app_url}"
}

# -----------------------------------------------------------------------------
# Pre-flight Checks
# -----------------------------------------------------------------------------

preflight_checks() {
    # Check Railway CLI
    if ! command -v railway &> /dev/null; then
        log_error "Railway CLI not installed. Run ./deploy.sh first."
        exit 1
    fi

    # Check authentication
    if ! railway whoami &> /dev/null; then
        log_error "Not authenticated with Railway. Run 'railway login'."
        exit 1
    fi

    # Check if project is linked
    cd "${PROJECT_ROOT}"
    if ! railway status &> /dev/null; then
        log_error "No Railway project linked. Run ./deploy.sh first."
        exit 1
    fi
}

# -----------------------------------------------------------------------------
# Load From File
# -----------------------------------------------------------------------------

load_from_file() {
    if [ ! -f "${ENV_FILE}" ]; then
        log_error "Environment file not found: ${ENV_FILE}"
        exit 1
    fi

    log_info "Loading environment variables from: ${ENV_FILE}"

    cd "${PROJECT_ROOT}"

    # Read file and set variables
    while IFS='=' read -r key value || [ -n "$key" ]; do
        # Skip empty lines and comments
        [[ -z "$key" || "$key" =~ ^# ]] && continue

        # Remove quotes from value
        value=$(echo "$value" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")

        # Skip if value is empty or a placeholder
        [[ -z "$value" || "$value" == "your-"* ]] && continue

        log_info "Setting: $key"
        railway variables --set "${key}=${value}" --skip-deploys
    done < "${ENV_FILE}"

    log_success "Environment variables loaded from file"
}

# -----------------------------------------------------------------------------
# Email Configuration
# -----------------------------------------------------------------------------

configure_email() {
    echo ""
    echo "=============================================="
    echo "Resend Email Configuration"
    echo "=============================================="
    echo ""
    log_info "Resend provides 3,000 emails/month on the free tier"
    log_info "Get your API key at: https://resend.com/api-keys"
    echo ""

    read -p "Enter Resend API key: " RESEND_API_KEY
    read -p "Enter 'From' email address (must be verified in Resend): " EMAIL_FROM_ADDRESS
    read -p "Enter 'From' display name [Litestar App]: " EMAIL_FROM_NAME
    EMAIL_FROM_NAME="${EMAIL_FROM_NAME:-Litestar App}"

    log_info "Configuring Resend..."

    cd "${PROJECT_ROOT}"

    railway variables --set "EMAIL_ENABLED=true" \
        --set "EMAIL_BACKEND=resend" \
        --set "EMAIL_FROM_ADDRESS=${EMAIL_FROM_ADDRESS}" \
        --set "EMAIL_FROM_NAME=${EMAIL_FROM_NAME}" \
        --set "RESEND_API_KEY=${RESEND_API_KEY}"

    log_success "Resend configured successfully"
    log_info "Redeploy to apply changes: ./deploy.sh"
}

# -----------------------------------------------------------------------------
# GitHub OAuth Configuration
# -----------------------------------------------------------------------------

configure_github_oauth() {
    echo ""
    echo "=============================================="
    echo "GitHub OAuth App Configuration"
    echo "=============================================="
    echo ""
    log_info "GitHub OAuth Apps must be created manually."
    log_info "We'll open the GitHub developer settings page and then set Railway vars."
    echo ""

    cd "${PROJECT_ROOT}"

    local app_url=""
    local callback_url=""
    app_url="$(get_app_url)"
    if [ -z "${app_url}" ]; then
        read -p "Enter your public app URL (e.g. https://your-app.up.railway.app): " app_url
    fi

    app_url="${app_url%/}"
    callback_url="${app_url}/api/auth/oauth/github/callback"

    echo ""
    echo "Use these values when creating the OAuth App:"
    echo "  Homepage URL: ${app_url}"
    echo "  Authorization callback URL: ${callback_url}"
    echo ""
    echo "Create the app here:"
    echo "  https://github.com/settings/developers"
    echo ""

    if command -v gh &> /dev/null; then
        if ! gh auth status &> /dev/null; then
            log_warn "GitHub CLI not authenticated."
            read -p "Login with 'gh auth login -w'? [y/N]: " login_choice
            if [[ "${login_choice}" =~ ^[Yy]$ ]]; then
                gh auth login -w || true
            fi
        fi

        read -p "Open GitHub developer settings in your browser now? [y/N]: " open_choice
        if [[ "${open_choice}" =~ ^[Yy]$ ]]; then
            if ! gh browse "https://github.com/settings/developers" &> /dev/null; then
                log_warn "Could not open browser via gh. Open the URL manually."
            fi
        fi
    else
        log_warn "GitHub CLI (gh) not installed."
        log_info "Install it from https://cli.github.com/ if you want browser integration."
    fi

    echo ""
    read -p "Enter GitHub OAuth Client ID: " GITHUB_OAUTH2_CLIENT_ID
    read -s -p "Enter GitHub OAuth Client Secret: " GITHUB_OAUTH2_CLIENT_SECRET
    echo ""

    if [ -z "${GITHUB_OAUTH2_CLIENT_ID}" ] || [ -z "${GITHUB_OAUTH2_CLIENT_SECRET}" ]; then
        log_error "Client ID and Secret are required."
        exit 1
    fi

    log_info "Saving GitHub OAuth credentials to Railway..."
    railway variables --set "GITHUB_OAUTH2_CLIENT_ID=${GITHUB_OAUTH2_CLIENT_ID}" \
        --set "GITHUB_OAUTH2_CLIENT_SECRET=${GITHUB_OAUTH2_CLIENT_SECRET}"

    log_success "GitHub OAuth configured successfully"
    log_info "Redeploy to apply changes: ./deploy.sh"
}

# -----------------------------------------------------------------------------
# Set Single Variable
# -----------------------------------------------------------------------------

set_variable() {
    if [[ ! "${SET_VAR}" =~ = ]]; then
        log_error "Invalid format. Use: --set KEY=VALUE"
        exit 1
    fi

    cd "${PROJECT_ROOT}"
    railway variables --set "${SET_VAR}"
    log_success "Variable set: ${SET_VAR%%=*}"
}

# -----------------------------------------------------------------------------
# Display Variables
# -----------------------------------------------------------------------------

display_variables() {
    echo ""
    echo "=============================================="
    echo "Current Environment Variables"
    echo "=============================================="

    cd "${PROJECT_ROOT}"
    railway variables

    echo ""
}

# -----------------------------------------------------------------------------
# Interactive Menu
# -----------------------------------------------------------------------------

main_menu() {
    echo ""
    echo "=============================================="
    echo "Railway Environment Configuration"
    echo "=============================================="
    echo ""
    echo "Options:"
    echo "  1. View current variables"
    echo "  2. Configure Resend for email"
    echo "  3. Configure GitHub OAuth"
    echo "  4. Set custom variable"
    echo "  5. Load from .env file"
    echo "  6. Exit"
    echo ""

    read -p "Select option (1-6): " choice

    cd "${PROJECT_ROOT}"

    case $choice in
        1)
            display_variables
            main_menu
            ;;
        2)
            configure_email
            main_menu
            ;;
        3)
            configure_github_oauth
            main_menu
            ;;
        4)
            read -p "Variable (KEY=VALUE): " var_input
            railway variables --set "${var_input}"
            log_success "Variable set: ${var_input%%=*}"
            main_menu
            ;;
        5)
            read -p "Path to .env file: " env_path
            ENV_FILE="${env_path}"
            load_from_file
            main_menu
            ;;
        6)
            log_info "Exiting..."
            exit 0
            ;;
        *)
            log_error "Invalid selection"
            main_menu
            ;;
    esac
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

main() {
    preflight_checks

    # Handle specific flags
    if [ -n "${ENV_FILE}" ]; then
        load_from_file
        exit 0
    fi

    if [ -n "${SET_VAR}" ]; then
        set_variable
        exit 0
    fi

    if [ "${CONFIGURE_EMAIL}" = true ]; then
        configure_email
        exit 0
    fi

    if [ "${CONFIGURE_GITHUB_OAUTH}" = true ]; then
        configure_github_oauth
        exit 0
    fi

    # Otherwise, show interactive menu
    main_menu
}

main "$@"
