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

# Service names (can be customized if renamed in Railway dashboard)
APP_SERVICE_NAME="${APP_SERVICE_NAME:-Litestar Web Frontend}"
WORKER_SERVICE_NAME="${WORKER_SERVICE_NAME:-SAQ Worker}"

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
# Redis Provisioning (for SAQ background tasks)
# -----------------------------------------------------------------------------

ensure_redis() {
    log_info "Checking Redis for SAQ..."
    cd "${PROJECT_ROOT}"

    # Check if Redis service already exists
    if railway status --json 2>/dev/null | grep -qi 'redis'; then
        log_success "Redis already provisioned"
        return 0
    fi

    log_info "Provisioning Redis for SAQ background tasks..."
    railway add --database redis
    log_success "Redis provisioned"
}

# -----------------------------------------------------------------------------
# App Service Setup
# -----------------------------------------------------------------------------

ensure_app_service() {
    log_info "Checking application service..."
    cd "${PROJECT_ROOT}"

    # Check if app service already exists
    if railway status --json 2>/dev/null | grep -qi "\"${APP_SERVICE_NAME}\""; then
        log_success "Application service already exists"
        railway service link "${APP_SERVICE_NAME}" 2>/dev/null || true
        return 0
    fi

    log_info "Creating application service..."
    railway add --service "${APP_SERVICE_NAME}"
    railway service link "${APP_SERVICE_NAME}"
    log_success "Application service created and linked"
}

# -----------------------------------------------------------------------------
# Worker Service Setup
# -----------------------------------------------------------------------------

ensure_worker_service() {
    log_info "Checking background worker service..."
    cd "${PROJECT_ROOT}"

    if railway status --json 2>/dev/null | grep -qi "\"${WORKER_SERVICE_NAME}\""; then
        log_success "Worker service already exists"
        railway service link "${WORKER_SERVICE_NAME}" 2>/dev/null || true
        return 0
    fi

    log_info "Creating background worker service..."
    railway add --service "${WORKER_SERVICE_NAME}"
    railway service link "${WORKER_SERVICE_NAME}"
    log_success "Worker service created"
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

        # Ensure LITESTAR_PORT references Railway's injected PORT
        if ! railway variables --kv 2>/dev/null | grep -q 'LITESTAR_PORT=\${{PORT}}'; then
            log_info "Setting LITESTAR_PORT to use Railway's PORT..."
            railway variables --set 'LITESTAR_PORT=${{PORT}}' --skip-deploys
        fi

        # Ensure SQLAlchemy logs are quiet by default
        if ! railway variables --kv 2>/dev/null | grep -q "SQLALCHEMY_LOG_LEVEL="; then
            log_info "Setting SQLALCHEMY_LOG_LEVEL=30 (WARNING)..."
            railway variables --set "SQLALCHEMY_LOG_LEVEL=30" --skip-deploys
        fi

        # Ensure SAQ_REDIS_URL is set (for existing deployments without Redis)
        if ! railway variables --kv 2>/dev/null | grep -q "SAQ_REDIS_URL="; then
            log_info "Setting SAQ_REDIS_URL for background tasks..."
            railway variables --set 'SAQ_REDIS_URL=${{Redis.REDIS_URL}}' --skip-deploys
        fi

        # Ensure LITESTAR_TRUSTED_PROXIES is set (for OAuth redirect URL protocol)
        if ! railway variables --kv 2>/dev/null | grep -q "LITESTAR_TRUSTED_PROXIES="; then
            log_info "Setting LITESTAR_TRUSTED_PROXIES=* for proxy header support..."
            railway variables --set "LITESTAR_TRUSTED_PROXIES=*" --skip-deploys
        fi
        return 0
    fi

    # Generate a secure secret key
    SECRET_KEY=$(openssl rand -base64 32 | tr -d '=' | tr '+/' '-_')

    # Set essential variables
    # Note: Railway injects PORT automatically, we reference it for LITESTAR_PORT
    railway variables --set "SECRET_KEY=${SECRET_KEY}" \
        --set "LITESTAR_DEBUG=false" \
        --set "VITE_DEV_MODE=false" \
        --set "LITESTAR_TRUSTED_PROXIES=*" \
        --set "DATABASE_ECHO=false" \
        --set "SQLALCHEMY_LOG_LEVEL=30" \
        --set "EMAIL_ENABLED=false" \
        --set "EMAIL_BACKEND=console" \
        --set 'LITESTAR_PORT=${{PORT}}' \
        --set 'DATABASE_URL=${{Postgres.DATABASE_URL}}' \
        --set 'SAQ_REDIS_URL=${{Redis.REDIS_URL}}' \
        --set 'APP_URL=https://${{RAILWAY_PUBLIC_DOMAIN}}' \
        --skip-deploys

    log_success "Environment variables configured"
    log_info "  - DATABASE_URL: linked to Postgres service"
    log_info "  - SAQ_REDIS_URL: linked to Redis service"
    log_info "  - APP_URL: auto-configured from Railway domain"
    log_info "  - LITESTAR_PORT: uses Railway's injected PORT"
}

# -----------------------------------------------------------------------------
# Service Configuration
# -----------------------------------------------------------------------------

configure_app_service() {
    log_info "Configuring app service..."
    cd "${PROJECT_ROOT}"
    railway service link "${APP_SERVICE_NAME}"

    local current_vars
    current_vars=$(railway variables --kv 2>/dev/null || echo "")

    # Only update if not already configured
    if ! echo "$current_vars" | grep -q "SAQ_USE_SERVER_LIFESPAN=false"; then
        log_info "Setting app service environment variables..."
        # NOTE: SAQ_USE_SERVER_LIFESPAN=false because worker runs separately
        # Start command is defined in Dockerfile CMD or Railway dashboard settings
        railway variables \
            --set "SAQ_USE_SERVER_LIFESPAN=false" \
            --skip-deploys
    fi

    log_success "App service configured"
    log_info "  NOTE: Verify in Railway dashboard that:"
    log_info "    - Dockerfile: tools/deploy/docker/Dockerfile.distroless"
    log_info "    - Config file: tools/deploy/railway/railway.app.json"
    log_info "    - Health check: /health (timeout 300s)"
}

configure_worker_service() {
    log_info "Configuring worker service..."
    cd "${PROJECT_ROOT}"
    railway service link "${WORKER_SERVICE_NAME}"

    local current_vars
    current_vars=$(railway variables --kv 2>/dev/null || echo "")

    # Set worker-specific environment variables
    if ! echo "$current_vars" | grep -q "SAQ_USE_SERVER_LIFESPAN=false"; then
        log_info "Setting worker service environment variables..."
        # NOTE: Worker runs independently, not tied to server lifespan
        railway variables \
            --set "SAQ_USE_SERVER_LIFESPAN=false" \
            --skip-deploys
    fi

    # Copy shared variables from app service if worker doesn't have them
    if ! echo "$current_vars" | grep -q "SECRET_KEY="; then
        log_info "Copying shared environment variables to worker..."

        railway service link "${APP_SERVICE_NAME}"
        local secret_key
        secret_key=$(railway variables --kv 2>/dev/null | grep "SECRET_KEY=" | cut -d'=' -f2-)

        railway service link "${WORKER_SERVICE_NAME}"
        railway variables \
            --set "SECRET_KEY=${secret_key}" \
            --set "LITESTAR_DEBUG=false" \
            --set "DATABASE_ECHO=false" \
            --set "SQLALCHEMY_LOG_LEVEL=30" \
            --set 'DATABASE_URL=${{Postgres.DATABASE_URL}}' \
            --set 'SAQ_REDIS_URL=${{Redis.REDIS_URL}}' \
            --skip-deploys
    fi

    log_success "Worker service configured"
    log_warn "IMPORTANT: Configure worker service in Railway dashboard:"
    log_info "  1. Settings → Deploy → Dockerfile Path: tools/deploy/docker/Dockerfile.worker"
    log_info "  2. Settings → Deploy → Config file: tools/deploy/railway/railway.worker.json"
    log_info "  3. Settings → Deploy → Serverless: DISABLED (worker cannot wake from HTTP)"
    log_info "  4. Settings → Deploy → Health check: DISABLED (no HTTP endpoint)"
}

# -----------------------------------------------------------------------------
# Metal Builds
# -----------------------------------------------------------------------------

enable_metal_builds() {
    log_info "Enabling metal builds on all services..."
    cd "${PROJECT_ROOT}"

    # Enable on app service
    railway service link "${APP_SERVICE_NAME}"
    if ! railway variables --kv 2>/dev/null | grep -q "RAILWAY_USE_METAL_BUILDS=true"; then
        railway variables --set "RAILWAY_USE_METAL_BUILDS=true" --skip-deploys
    fi

    # Enable on worker service
    railway service link "${WORKER_SERVICE_NAME}"
    if ! railway variables --kv 2>/dev/null | grep -q "RAILWAY_USE_METAL_BUILDS=true"; then
        railway variables --set "RAILWAY_USE_METAL_BUILDS=true" --skip-deploys
    fi

    log_success "Metal builds enabled on all app services"
    log_info "Note: Database metal builds and sizing must be configured in Railway dashboard"
    log_info "  - Postgres: Set to 2 CPU / 2 GB RAM"
    log_info "  - Redis: Set to smallest available instance"
}

# -----------------------------------------------------------------------------
# Build Verification
# -----------------------------------------------------------------------------

verify_build() {
    log_info "Verifying build configuration..."

    cd "${PROJECT_ROOT}"

    # Check Dockerfiles exist
    if [ ! -f "tools/deploy/docker/Dockerfile.distroless" ]; then
        log_error "Dockerfile not found at tools/deploy/docker/Dockerfile.distroless"
        exit 1
    fi

    if [ ! -f "tools/deploy/docker/Dockerfile.worker" ]; then
        log_error "Worker Dockerfile not found at tools/deploy/docker/Dockerfile.worker"
        exit 1
    fi

    # Check Railway configs exist
    if [ ! -f "tools/deploy/railway/railway.app.json" ]; then
        log_error "railway.app.json not found at tools/deploy/railway/railway.app.json"
        exit 1
    fi

    if [ ! -f "tools/deploy/railway/railway.worker.json" ]; then
        log_error "railway.worker.json not found at tools/deploy/railway/railway.worker.json"
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

    # Always use detached mode to avoid hanging on health checks
    # Deploy app service
    log_info "Deploying app service..."
    railway service link "${APP_SERVICE_NAME}"
    railway up --detach

    # Deploy worker service
    log_info "Deploying worker service..."
    railway service link "${WORKER_SERVICE_NAME}"
    railway up --detach

    log_success "Deployment started"
    log_info "Use 'railway logs' to monitor deployment"
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
    echo "Services:"
    echo "  - App service: Litestar web server (1 CPU / 1 GB RAM)"
    echo "  - Worker service: SAQ background tasks (1 CPU / 1 GB RAM)"
    echo ""
    echo "Infrastructure:"
    echo "  - PostgreSQL database (DATABASE_URL)"
    echo "  - Redis for SAQ background tasks (SAQ_REDIS_URL)"
    echo "  - Public domain (APP_URL auto-detected)"
    echo "  - Serverless: DISABLED (worker cannot wake from HTTP)"
    echo "  - Metal builds enabled"
    echo ""
    echo "Useful commands:"
    echo "  railway open                      - Open Railway dashboard"
    echo "  railway service link \"${APP_SERVICE_NAME}\" && railway logs   - View app logs"
    echo "  railway service link \"${WORKER_SERVICE_NAME}\" && railway logs - View worker logs"
    echo "  railway status                    - Check deployment status"
    echo ""
    echo -e "${YELLOW}REQUIRED manual configuration in Railway dashboard:${NC}"
    echo ""
    echo "  1. App Service (${APP_SERVICE_NAME}):"
    echo "     Settings → Deploy → Dockerfile Path: tools/deploy/docker/Dockerfile.distroless"
    echo "     Settings → Deploy → Config file: tools/deploy/railway/railway.app.json"
    echo ""
    echo "  2. Worker Service (${WORKER_SERVICE_NAME}):"
    echo "     Settings → Deploy → Dockerfile Path: tools/deploy/docker/Dockerfile.worker"
    echo "     Settings → Deploy → Config file: tools/deploy/railway/railway.worker.json"
    echo "     Settings → Deploy → Serverless: DISABLED"
    echo "     Settings → Deploy → Health check: DISABLED"
    echo ""
    echo "  3. Database Resources:"
    echo "     - Postgres: 2 CPU / 2 GB RAM, enable Metal builds"
    echo "     - Redis: Smallest instance, enable Metal builds"
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
        ensure_redis
        ensure_app_service
        ensure_worker_service
        ensure_domain
        ensure_environment
        configure_app_service
        configure_worker_service
        enable_metal_builds
    fi

    # Build verification
    verify_build

    # Deploy
    deploy

    # Skip health check - deployments are async, check via 'railway status' or dashboard

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
