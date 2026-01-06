#!/usr/bin/env bash
# =============================================================================
# Railway Deployment Script (Unified)
# =============================================================================
# This script handles the complete Railway deployment workflow:
#   - Project setup (if not already configured)
#   - Environment variable configuration
#   - Database provisioning
#   - Application deployment
#
# Usage:
#   ./deploy.sh [OPTIONS]
#
# Options:
#   --detach          Don't wait for deployment to complete
#   --skip-setup      Skip setup checks (assumes already configured)
#   --email           Configure Resend email after deployment
#   --github-oauth    Configure GitHub OAuth after deployment
#
# The script is fully idempotent - safe to run multiple times.
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DETACH=false
SKIP_SETUP=false
CONFIGURE_EMAIL=false
CONFIGURE_GITHUB_OAUTH=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
PROJECT_NAME=""
EXISTING_PROJECT=false

# -----------------------------------------------------------------------------
# Parse Arguments
# -----------------------------------------------------------------------------

while [[ $# -gt 0 ]]; do
    case $1 in
        --detach)
            DETACH=true
            shift
            ;;
        --skip-setup)
            SKIP_SETUP=true
            shift
            ;;
        --email)
            CONFIGURE_EMAIL=true
            shift
            ;;
        --github-oauth)
            CONFIGURE_GITHUB_OAUTH=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./deploy.sh [--detach] [--skip-setup] [--email] [--github-oauth]"
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

check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

run_env_setup() {
    "${SCRIPT_DIR}/env-setup.sh" "$@"
}

# -----------------------------------------------------------------------------
# Railway CLI Setup
# -----------------------------------------------------------------------------

ensure_railway_cli() {
    if check_command railway; then
        log_info "Railway CLI: $(railway --version)"
        return 0
    fi

    log_info "Installing Railway CLI..."

    if ! check_command npm; then
        log_error "npm is required to install Railway CLI"
        log_info "Install Node.js from https://nodejs.org/"
        exit 1
    fi

    npm install -g @railway/cli

    if check_command railway; then
        log_success "Railway CLI installed: $(railway --version)"
    else
        log_error "Failed to install Railway CLI"
        exit 1
    fi
}

# -----------------------------------------------------------------------------
# Authentication
# -----------------------------------------------------------------------------

ensure_authenticated() {
    if railway whoami &> /dev/null; then
        log_info "Authenticated as: $(railway whoami)"
        return 0
    fi

    log_info "Please authenticate with Railway..."
    railway login

    if railway whoami &> /dev/null; then
        log_success "Authenticated as: $(railway whoami)"
    else
        log_error "Authentication failed"
        exit 1
    fi
}

# -----------------------------------------------------------------------------
# Project Detection/Creation
# -----------------------------------------------------------------------------

check_existing_project() {
    cd "${PROJECT_ROOT}"

    # Check if already linked to a Railway project
    if railway status &> /dev/null; then
        # Extract project name from status
        PROJECT_NAME=$(railway status --json 2>/dev/null | grep -o '"name": *"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")
        if [ -n "${PROJECT_NAME}" ]; then
            log_success "Linked to project: ${PROJECT_NAME}"
            EXISTING_PROJECT=true
            return 0
        fi
    fi

    EXISTING_PROJECT=false
}

ensure_project() {
    if [ "${EXISTING_PROJECT}" = true ]; then
        return 0
    fi

    echo ""
    read -p "Enter project name [litestar-fullstack-spa]: " PROJECT_NAME
    PROJECT_NAME="${PROJECT_NAME:-litestar-fullstack-spa}"
    echo ""

    log_info "Creating Railway project: ${PROJECT_NAME}"
    cd "${PROJECT_ROOT}"
    railway init --name "${PROJECT_NAME}"
    log_success "Project created: ${PROJECT_NAME}"
}

# -----------------------------------------------------------------------------
# Database Provisioning
# -----------------------------------------------------------------------------

ensure_database() {
    log_info "Checking PostgreSQL database..."
    cd "${PROJECT_ROOT}"

    # Check if Postgres service already exists
    if railway status --json 2>/dev/null | grep -qi 'postgres'; then
        log_success "PostgreSQL database already provisioned"
        return 0
    fi

    log_info "Provisioning PostgreSQL database..."
    railway add --database postgres
    log_success "PostgreSQL database provisioned"
}

# -----------------------------------------------------------------------------
# App Service Setup
# -----------------------------------------------------------------------------

ensure_app_service() {
    log_info "Checking application service..."
    cd "${PROJECT_ROOT}"

    # Check if app service already exists
    if railway status --json 2>/dev/null | grep -qi '"app"'; then
        log_success "Application service already exists"
        railway service link app 2>/dev/null || true
        return 0
    fi

    log_info "Creating application service..."
    railway add --service "app"
    railway service link app
    log_success "Application service created and linked"
}

# -----------------------------------------------------------------------------
# Domain Generation
# -----------------------------------------------------------------------------

ensure_domain() {
    log_info "Checking public domain..."
    cd "${PROJECT_ROOT}"

    # Check if domain already exists
    if railway domain --json 2>/dev/null | grep -q 'railway.app'; then
        log_success "Public domain already configured"
        return 0
    fi

    log_info "Generating public domain..."
    railway domain
    log_success "Public domain generated"
}

# -----------------------------------------------------------------------------
# Environment Variables
# -----------------------------------------------------------------------------

ensure_environment() {
    log_info "Configuring environment variables..."
    cd "${PROJECT_ROOT}"

    # Check if already configured (SECRET_KEY exists)
    if railway variables --kv 2>/dev/null | grep -q "SECRET_KEY="; then
        log_success "Environment variables already configured"

        # Always ensure PORT is set (may need update)
        if ! railway variables --kv 2>/dev/null | grep -q "PORT=8080"; then
            log_info "Updating PORT configuration..."
            railway variables --set "PORT=8080" --set "LITESTAR_PORT=8080" --skip-deploys
        fi

        # Ensure SQLAlchemy logs are quiet by default
        if ! railway variables --kv 2>/dev/null | grep -q "SQLALCHEMY_LOG_LEVEL="; then
            log_info "Setting SQLALCHEMY_LOG_LEVEL=30 (WARNING)..."
            railway variables --set "SQLALCHEMY_LOG_LEVEL=30" --skip-deploys
        fi
        return 0
    fi

    # Generate a secure secret key
    SECRET_KEY=$(openssl rand -base64 32 | tr -d '=' | tr '+/' '-_')

    # Set essential variables
    railway variables --set "SECRET_KEY=${SECRET_KEY}" \
        --set "LITESTAR_DEBUG=false" \
        --set "VITE_DEV_MODE=false" \
        --set "DATABASE_ECHO=false" \
        --set "SQLALCHEMY_LOG_LEVEL=30" \
        --set "EMAIL_ENABLED=false" \
        --set "EMAIL_BACKEND=console" \
        --set "PORT=8080" \
        --set "LITESTAR_PORT=8080" \
        --set 'DATABASE_URL=${{Postgres.DATABASE_URL}}' \
        --set 'APP_URL=https://${{RAILWAY_PUBLIC_DOMAIN}}' \
        --skip-deploys

    log_success "Environment variables configured"
    log_info "  - DATABASE_URL: linked to Postgres service"
    log_info "  - APP_URL: auto-configured from Railway domain"
    log_info "  - PORT/LITESTAR_PORT: 8080"
}

# -----------------------------------------------------------------------------
# Metal Builds
# -----------------------------------------------------------------------------

enable_metal_builds() {
    log_info "Checking metal builds..."
    cd "${PROJECT_ROOT}"

    if railway variables --kv 2>/dev/null | grep -q "RAILWAY_USE_METAL_BUILDS=true"; then
        log_success "Metal builds already enabled"
        return 0
    fi

    railway variables --set "RAILWAY_USE_METAL_BUILDS=true" --skip-deploys
    log_success "Metal builds enabled"
}

# -----------------------------------------------------------------------------
# Build Verification
# -----------------------------------------------------------------------------

verify_build() {
    log_info "Verifying build configuration..."

    cd "${PROJECT_ROOT}"

    # Check Dockerfile exists
    if [ ! -f "tools/deploy/docker/Dockerfile.distroless" ]; then
        log_error "Dockerfile not found at tools/deploy/docker/Dockerfile.distroless"
        exit 1
    fi

    # Check railway.json exists
    if [ ! -f "railway.json" ]; then
        log_error "railway.json not found in project root"
        exit 1
    fi

    log_success "Build configuration verified"
}

# -----------------------------------------------------------------------------
# Deployment
# -----------------------------------------------------------------------------

deploy() {
    log_info "Starting deployment..."

    cd "${PROJECT_ROOT}"

    if [ "${DETACH}" = true ]; then
        railway up --detach
        log_success "Deployment started (detached mode)"
        log_info "Use 'railway logs' to monitor deployment"
    else
        railway up
        log_success "Deployment complete"
    fi
}

# -----------------------------------------------------------------------------
# Health Check
# -----------------------------------------------------------------------------

health_check() {
    log_info "Checking deployment health..."

    cd "${PROJECT_ROOT}"

    # Get the deployment URL
    DEPLOY_URL=$(railway status --json 2>/dev/null | grep -o '"url": *"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")

    if [ -z "${DEPLOY_URL}" ]; then
        log_warn "Could not determine deployment URL"
        log_info "Check Railway dashboard for deployment status"
        return 0
    fi

    # Wait a moment for the service to start
    sleep 5

    # Check health endpoint
    if curl -sf "${DEPLOY_URL}/health" > /dev/null 2>&1; then
        log_success "Health check passed: ${DEPLOY_URL}/health"
    else
        log_warn "Health check failed or pending. The service may still be starting."
        log_info "Check status: railway logs"
    fi
}

# -----------------------------------------------------------------------------
# Display Summary
# -----------------------------------------------------------------------------

display_summary() {
    cd "${PROJECT_ROOT}"

    echo ""
    echo "=============================================="
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo "=============================================="
    echo ""
    echo "Project: ${PROJECT_NAME:-$(railway status --json 2>/dev/null | grep -o '"name": *"[^"]*"' | head -1 | cut -d'"' -f4 || echo 'Unknown')}"
    echo ""
    echo "Configuration:"
    echo "  - PostgreSQL database with shared DATABASE_URL"
    echo "  - Public domain (APP_URL auto-detected)"
    echo "  - PORT/LITESTAR_PORT: 8080"
    echo "  - Dockerfile.distroless builder"
    echo "  - 2 CPU / 2 GB RAM limits"
    echo ""
    echo "Useful commands:"
    echo "  railway open     - Open Railway dashboard"
    echo "  railway logs     - View application logs"
    echo "  railway status   - Check deployment status"
    echo "  railway run bash - SSH into container"
    echo ""
    if [ "${CONFIGURE_EMAIL}" = false ]; then
        echo "To configure email:"
        echo "  ./deploy.sh --email"
        echo "  ./env-setup.sh --email"
        echo ""
    fi
    if [ "${CONFIGURE_GITHUB_OAUTH}" = false ]; then
        echo "To configure GitHub OAuth:"
        echo "  ./deploy.sh --github-oauth"
        echo "  ./env-setup.sh --github-oauth"
        echo ""
    fi
    echo "=============================================="
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

main() {
    echo ""
    echo "=============================================="
    echo "Railway Deployment"
    echo "=============================================="
    echo ""

    # Pre-flight
    ensure_railway_cli
    ensure_authenticated

    # Setup (if needed)
    if [ "${SKIP_SETUP}" = false ]; then
        check_existing_project
        ensure_project
        ensure_database
        ensure_app_service
        ensure_domain
        ensure_environment
        enable_metal_builds
    fi

    # Build verification
    verify_build

    # Deploy
    deploy

    # Health check (if not detached)
    if [ "${DETACH}" = false ]; then
        health_check
    fi

    # Optional configs
    if [ "${CONFIGURE_EMAIL}" = true ]; then
        run_env_setup --email
    fi

    if [ "${CONFIGURE_GITHUB_OAUTH}" = true ]; then
        run_env_setup --github-oauth
    fi

    display_summary
}

main "$@"
