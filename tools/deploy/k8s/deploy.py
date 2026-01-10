#!/usr/bin/env -S uv run python
# ruff: noqa: BLE001, FIX002
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "richclick",
#     "jinja2",
#     "structlog",
#     "python-dotenv",
#     "click",
# ]
# ///
import base64
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import rich_click as click
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from rich.console import Console
from rich.panel import Panel

# --- Configuration ---

REQUIRED_SECRETS = [
    "SECRET_KEY",
    "DATABASE_PASSWORD",
]

# Optional secrets that will be included if present in .env
OPTIONAL_SECRETS = [
    "RESEND_API_KEY",
    "GITHUB_OAUTH2_CLIENT_ID",
    "GITHUB_OAUTH2_CLIENT_SECRET",
    "GOOGLE_OAUTH2_CLIENT_ID",
    "GOOGLE_OAUTH2_CLIENT_SECRET",
]

BASE_DIR = Path(__file__).parent
TEMPLATE_DIR = BASE_DIR / "templates"
KUBECTL_CMD = "kubectl"

# Define environment-specific configurations
# TODO: Add/adjust values based on your needs
CONFIG: dict[str, dict[str, Any]] = {
    "dev": {
        "namespace": "litestar-dev",
        "env": "dev",
        "image_tag": "latest",
        # Compute resources
        "api_replicas": 1,
        "worker_replicas": 1,
        "web_replicas": 1,
        "api_min_replicas": 1,
        "api_max_replicas": 3,
        "worker_min_replicas": 1,
        "worker_max_replicas": 3,
        "api_cpu_request": "100m",
        "api_mem_request": "256Mi",
        "api_cpu_limit": "500m",
        "api_mem_limit": "512Mi",
        "worker_cpu_request": "100m",
        "worker_mem_request": "256Mi",
        "worker_cpu_limit": "500m",
        "worker_mem_limit": "512Mi",
        # Database
        "db_name": "appdb",
        "db_user": "appuser",
        "db_host": "postgres-service",
        "db_port": "5432",
        "db_storage": "5Gi",
        "db_cpu_request": "100m",
        "db_mem_request": "256Mi",
        "db_cpu_limit": "500m",
        "db_mem_limit": "512Mi",
        "storage_class_name": None,  # Use default storage class
        # Redis
        "redis_host": "redis-service",
        "redis_port": "6379",
        "redis_storage": "1Gi",
        "redis_max_memory": "256mb",
        "redis_cpu_request": "50m",
        "redis_mem_request": "128Mi",
        "redis_cpu_limit": "200m",
        "redis_mem_limit": "256Mi",
        # Application
        "log_level": "DEBUG",
        "allowed_cors_origins": '["*"]',
        "api_workers": 1,
        "saq_concurrency": 10,
        "saq_web_enabled": "false",
        # HPA
        "hpa_cpu_target": 70,
        "hpa_mem_target": None,  # No memory target for dev HPA
        # Ingress
        "ingress_enabled": False,
        "ingress_host": None,
        "ingress_tls_secret": None,
        "cert_issuer": None,
        "ingress_class": "nginx",
        # Security
        "service_account_name": "litestar-app",
        "gcp_service_account": None,  # Set for GKE Workload Identity
        # Other
        "app_scratch_path": None,  # Optional scratch path for dev
    },
    "prod": {
        "namespace": "litestar-prod",
        "env": "prod",
        "image_tag": "latest",  # Should be overridden with a specific tag for prod deploys
        # Compute resources
        "api_replicas": 2,  # Start with minReplicas from HPA
        "worker_replicas": 2,  # Start with minReplicas from HPA
        "web_replicas": 2,  # Static content might need more replicas
        "api_min_replicas": 2,
        "api_max_replicas": 10,
        "worker_min_replicas": 2,
        "worker_max_replicas": 10,
        "api_cpu_request": "200m",
        "api_mem_request": "512Mi",
        "api_cpu_limit": "1000m",  # 1 vCPU
        "api_mem_limit": "1Gi",
        "worker_cpu_request": "200m",
        "worker_mem_request": "512Mi",
        "worker_cpu_limit": "1000m",
        "worker_mem_limit": "1Gi",
        # Database
        "db_name": "appdb",
        "db_user": "appuser",
        "db_host": "postgres-service",
        "db_port": "5432",
        "db_storage": "20Gi",  # More storage for prod
        "db_cpu_request": "250m",
        "db_mem_request": "512Mi",
        "db_cpu_limit": "1000m",
        "db_mem_limit": "1Gi",
        "storage_class_name": None,  # Use default or set to 'premium-rwo' for GKE
        # Redis
        "redis_host": "redis-service",
        "redis_port": "6379",
        "redis_storage": "5Gi",
        "redis_max_memory": "512mb",
        "redis_cpu_request": "100m",
        "redis_mem_request": "256Mi",
        "redis_cpu_limit": "500m",
        "redis_mem_limit": "512Mi",
        # Application
        "log_level": "INFO",
        "allowed_cors_origins": '["https://your-frontend-domain.com"]',  # IMPORTANT: Change this!
        "api_workers": 4,  # Adjust based on prod instance size/cores
        "saq_concurrency": 20,  # Adjust based on expected load
        "saq_web_enabled": "false",
        # HPA
        "hpa_cpu_target": 60,  # Lower target for better responsiveness
        "hpa_mem_target": 75,  # Add memory scaling for prod
        # Ingress
        "ingress_enabled": True,
        "ingress_host": "your-domain.com",  # IMPORTANT: Change this!
        "ingress_tls_secret": "your-domain-tls",  # cert-manager creates this
        "cert_issuer": "letsencrypt-prod",  # Adjust if needed
        "ingress_class": "nginx",
        "rate_limit_enabled": True,
        "rate_limit_rps": "100",
        "rate_limit_connections": "10",
        # Security
        "service_account_name": "litestar-app",
        "gcp_service_account": None,  # Set for GKE Workload Identity, e.g., "app-sa@project.iam.gserviceaccount.com"
        # Other
        "app_scratch_path": None,  # Optional scratch path for prod
    },
}

# Templates to render and apply (in order)
# Order matters: secrets/configs before deployments, services before HPAs
TEMPLATES_APPLY_ORDER = [
    "namespace.yaml.j2",
    "serviceaccount.yaml.j2",  # ServiceAccount for Workload Identity
    "secrets.yaml.j2",
    "configmap.yaml.j2",
    # Database
    "db-pvc.yaml.j2",
    "db-service.yaml.j2",
    "db-statefulset.yaml.j2",
    # Redis (required for SAQ worker)
    "redis-service.yaml.j2",
    "redis-statefulset.yaml.j2",
    # Services (must exist before deployments reference them)
    "api-service.yaml.j2",
    "web-service.yaml.j2",
    "nginx-config.yaml.j2",  # Nginx config needs to exist before deployment
    # Deployments
    "api-deployment.yaml.j2",
    "worker-deployment.yaml.j2",
    "web-deployment.yaml.j2",
    # Autoscaling and availability
    "api-hpa.yaml.j2",
    "worker-hpa.yaml.j2",
    "pdb.yaml.j2",  # PodDisruptionBudgets (prod only)
    "ingress.yaml.j2",  # Apply last, only if enabled
]

TEMPLATES_DELETE_ORDER = list(reversed(TEMPLATES_APPLY_ORDER))

# --- Rich Console ---
console = Console()

# --- Jinja Environment ---
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=False)  # noqa: S701

# --- Helper Functions ---


def run_kubectl(args: list[str], input_data: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Runs a kubectl command.

    Args:
        args: The arguments to pass to kubectl.
        input_data: The input data to pass to kubectl.
        check: Whether to raise an exception if the command fails.

    Raises:
        subprocess.CalledProcessError: If the command fails and check is True.

    Returns:
        The completed process.
    """
    cmd = [KUBECTL_CMD, *args]
    console.print(f"[dim]Executing: {' '.join(cmd)}[/dim]")
    try:
        result = subprocess.run(
            cmd,
            input=input_data.encode() if input_data else None,
            capture_output=True,
            check=check,  # Raises CalledProcessError if command fails
            text=True,
        )
        if result.stdout:
            console.print(f"[dim]{result.stdout}[/dim]")
        if result.stderr:
            # Print stderr even if check=False and it didn't error
            console.print(f"[yellow dim]{result.stderr}[/yellow dim]")
        return result
    except FileNotFoundError:
        console.print(
            f"[bold red]Error: '{KUBECTL_CMD}' command not found. Is kubectl installed and in your PATH?[/bold red]"
        )
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        console.print("[bold red]Error executing kubectl command:[/bold red]")
        console.print(f"Command: {' '.join(e.cmd)}")
        console.print(f"Return Code: {e.returncode}")
        console.print(f"Stderr:\n{e.stderr}")
        console.print(f"Stdout:\n{e.stdout}")
        # Re-raise the error if check was True, otherwise just report
        if check:
            raise
        # Explicitly return the error object if check is False. Type checker might complain.
        # Consider a more robust error handling strategy if needed.
        return e  # type: ignore
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred while running kubectl: {e}[/bold red]")
        sys.exit(1)


def render_template(template_name: str, context: dict[str, Any]) -> str:
    """Renders a Jinja template.

    Args:
        template_name: The name of the template to render.
        context: The context to pass to the template.

    Returns:
        The rendered template.
    """
    try:
        template = jinja_env.get_template(template_name)
        return template.render(context)
    except Exception as e:
        console.print(f"[bold red]Error rendering template {template_name}: {e}[/bold red]")
        sys.exit(1)


def apply_manifest(rendered_yaml: str, namespace: str) -> None:
    """Applies a rendered YAML manifest using kubectl apply -f -."""
    console.print(f"[cyan]Applying manifest in namespace '{namespace}'...[/cyan]")
    run_kubectl(["apply", "-n", namespace, "-f", "-"], input_data=rendered_yaml)


def delete_manifest(rendered_yaml: str, namespace: str) -> None:
    """Deletes resources from a rendered YAML manifest using kubectl delete -f -."""
    console.print(f"[yellow]Deleting manifest resources in namespace '{namespace}'...[/yellow]")
    # Use check=False because 'delete --ignore-not-found' returns 0 even if some resources weren't found
    run_kubectl(
        ["delete", "-n", namespace, "--ignore-not-found=true", "-f", "-"], input_data=rendered_yaml, check=False
    )


def check_kubectl() -> None:
    try:
        subprocess.run([KUBECTL_CMD, "version", "--client"], capture_output=True, check=True, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        console.print(
            f"[bold red]Error: Failed to run '{KUBECTL_CMD} version'. Is kubectl installed and in your PATH?[/bold red]"
        )
        if isinstance(e, subprocess.CalledProcessError):
            console.print(f"[dim]{e.stderr}[/dim]")
        sys.exit(1)


# --- Config Building Helpers ---


def build_deploy_config(
    env: str,
    api_image_repo: str,
    worker_image_repo: str | None,
    tag: str | None,
    gcp_service_account: str | None,
    scratch_path: str | None,
) -> dict[str, Any]:
    """Builds the deployment configuration from environment and CLI options."""
    config = CONFIG[env].copy()

    # Image configuration
    config["api_image_repo"] = api_image_repo
    config["worker_image_repo"] = worker_image_repo or api_image_repo
    config["image_repo"] = api_image_repo  # Legacy compatibility

    # Handle image tag
    if tag:
        config["image_tag"] = tag
        console.print(f"[yellow]Using provided image tag:[/yellow] {tag}")
    elif env == "prod":
        console.print("[bold red]Error: --tag is required for production deployments.[/bold red]")
        sys.exit(1)
    else:
        console.print(f"[yellow]Using default image tag for {env}:[/yellow] {config['image_tag']}")

    # Add secrets to config
    _add_secrets_to_config(config)

    # GCP Workload Identity
    if gcp_service_account:
        config["gcp_service_account"] = gcp_service_account
        console.print(f"[cyan]GKE Workload Identity enabled with GSA:[/cyan] {gcp_service_account}")

    # Scratch path
    if scratch_path:
        config["APP_SCRATCH_PATH"] = scratch_path
    elif config.get("app_scratch_path"):
        config["APP_SCRATCH_PATH"] = config["app_scratch_path"]

    return config


def _add_secrets_to_config(config: dict[str, Any]) -> None:
    """Adds base64-encoded secrets to the config dict."""
    # Required secrets
    config["secret_key_b64"] = base64.b64encode(os.environ["SECRET_KEY"].encode()).decode()
    config["database_password_b64"] = base64.b64encode(os.environ["DATABASE_PASSWORD"].encode()).decode()

    # Build full database URL
    db_password = os.environ["DATABASE_PASSWORD"]
    db_url = f"postgresql+asyncpg://{config['db_user']}:{db_password}@{config['db_host']}:{config['db_port']}/{config['db_name']}"
    config["database_url_b64"] = base64.b64encode(db_url.encode()).decode()

    # Optional secrets
    for secret_key in OPTIONAL_SECRETS:
        if os.environ.get(secret_key):
            config_key = f"{secret_key.lower()}_b64"
            config[config_key] = base64.b64encode(os.environ[secret_key].encode()).decode()


# --- Manifest Helpers ---


def apply_all_manifests(config: dict[str, Any]) -> None:
    """Renders and applies all manifests in order."""
    namespace = config["namespace"]
    env = config["env"]

    console.print(f"[cyan]Applying manifests for {env}...[/cyan]")
    for template_name in TEMPLATES_APPLY_ORDER:
        if template_name == "ingress.yaml.j2" and not config.get("ingress_enabled", False):
            continue

        console.print(f"\n[green]Processing template:[/green] {template_name}")
        rendered_yaml = render_template(template_name, config)
        apply_manifest(rendered_yaml, namespace)


# --- Wait Helpers ---


def wait_for_pod(namespace: str, app_label: str, timeout: str, resource_name: str) -> None:
    """Waits for a pod with the given app label to be ready."""
    console.print(f"\n[cyan]Waiting for {resource_name} pod in namespace '{namespace}'...[/cyan]")
    try:
        run_kubectl(
            ["wait", "--for=condition=ready", "pod", "-l", f"app={app_label}", "-n", namespace, f"--timeout={timeout}"]
        )
        console.print(f"[green]{resource_name} pod is ready.[/green]")
    except subprocess.CalledProcessError:
        console.print(f"[yellow]Warning: {resource_name} pod readiness check timed out or failed.[/yellow]")


def wait_for_deployments(namespace: str, deployments: list[str]) -> None:
    """Waits for deployment rollouts to complete."""
    for deployment_name in deployments:
        console.print(f"\n[cyan]Waiting for rollout status of deployment '{deployment_name}'...[/cyan]")
        try:
            run_kubectl(["rollout", "status", f"deployment/{deployment_name}", "-n", namespace, "--timeout=300s"])
            console.print(f"[green]Deployment '{deployment_name}' rollout complete.[/green]")
        except subprocess.CalledProcessError:
            console.print(f"[yellow]Warning: Rollout for '{deployment_name}' timed out or failed.[/yellow]")


def show_deployment_status(namespace: str, ingress_enabled: bool) -> None:
    """Shows the current deployment status."""
    console.print("\n[blue]--- Current Status ---[/blue]")
    run_kubectl(["get", "pods", "-n", namespace], check=False)
    run_kubectl(["get", "svc", "-n", namespace], check=False)
    if ingress_enabled:
        run_kubectl(["get", "ingress", "-n", namespace], check=False)
    console.print("[blue]--------------------[/blue]")


# --- Click Command Group ---
HELP_TEXT = """
[bold blue]Litestar Kubernetes Deployment Tool[/bold blue]

[bold]USAGE:[/bold]
  python deploy.py [COMMAND] [OPTIONS]

[bold]COMMANDS:[/bold]
  [green]deploy[/green]   Render and apply all manifests for a given environment ([cyan]dev[/cyan] or [cyan]prod[/cyan]).
  [green]delete[/green]   Delete all manifests for a given environment ([cyan]dev[/cyan] or [cyan]prod[/cyan]).

[bold]EXAMPLES:[/bold]
  [dim]# Deploy to development[/dim]
  python deploy.py deploy -e dev --env-file .env --api-image-repo gcr.io/my-project/app

  [dim]# Deploy to production with separate worker image[/dim]
  python deploy.py deploy -e prod --tag v1.2.3 --env-file .env \\
    --api-image-repo gcr.io/my-project/app \\
    --worker-image-repo gcr.io/my-project/app-worker

  [dim]# Deploy to GKE with Workload Identity[/dim]
  python deploy.py deploy -e prod --tag v1.2.3 --env-file .env \\
    --api-image-repo gcr.io/my-project/app \\
    --gcp-service-account app-sa@my-project.iam.gserviceaccount.com

  [dim]# Delete all resources from dev[/dim]
  python deploy.py delete -e dev --env-file .env

  [dim]# Delete all resources and the namespace from prod[/dim]
  python deploy.py delete -e prod --delete-namespace --delete-pvc --env-file .env

[bold]REQUIRED:[/bold]
  --env-file           Path to a .env file containing all required secrets and configuration.
  --api-image-repo     Docker image repository for the API container.

[bold]REQUIRED SECRETS IN .env:[/bold]
  SECRET_KEY         The application secret key (will be base64 encoded).
  DATABASE_PASSWORD  The database password (will be base64 encoded).

[bold]OPTIONAL SECRETS IN .env:[/bold]
  RESEND_API_KEY              Email service API key.
  GITHUB_OAUTH2_CLIENT_ID     GitHub OAuth client ID.
  GITHUB_OAUTH2_CLIENT_SECRET GitHub OAuth client secret.
  GOOGLE_OAUTH2_CLIENT_ID     Google OAuth client ID.
  GOOGLE_OAUTH2_CLIENT_SECRET Google OAuth client secret.

[bold]GKE WORKLOAD IDENTITY:[/bold]
  Use --gcp-service-account to bind the Kubernetes ServiceAccount to a GCP
  service account for secure access to GCP APIs without storing credentials.

[bold]NOTES:[/bold]
- All secrets must be provided via the [bold]--env-file[/bold] option.
- For production, always use a specific image tag (not 'latest').
- The tool deploys: API, Worker, Redis, PostgreSQL, and optional Ingress.
- Database migrations are not handled by this tool.
"""


@click.group()
def cli() -> None:
    """Manages Kubernetes deployments for the Litestar Fullstack SPA."""
    if len(sys.argv) == 1:
        console.print(Panel(HELP_TEXT, expand=False, border_style="blue"))
        sys.exit(0)


# --- Deploy Command ---
@cli.command()
@click.option("-e", "--env", type=click.Choice(["dev", "prod"]), required=True, help="Deployment environment.")
@click.option("-t", "--tag", type=str, default=None, help="Docker image tag to deploy (overrides default for env).")
@click.option("--api-image-repo", type=str, default="your-repo/litestar-app", help="Docker image repository for API.")
@click.option(
    "--worker-image-repo",
    type=str,
    default=None,
    help="Docker image repository for worker (defaults to api-image-repo if not set).",
)
@click.option("--skip-db-wait", is_flag=True, default=False, help="Skip waiting for the database pod to be ready.")
@click.option("--skip-redis-wait", is_flag=True, default=False, help="Skip waiting for the Redis pod to be ready.")
@click.option("--skip-rollout-wait", is_flag=True, default=False, help="Skip waiting for deployment rollouts.")
@click.option(
    "--env-file",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=str),
    required=True,
    help="Path to a .env file to load secrets/config from (using python-dotenv).",
)
@click.option(
    "--scratch-path",
    type=str,
    default=None,
    help="Optional: Enable a scratch volume and mount it at this path (e.g. /tmp/app).",
)
@click.option(
    "--gcp-service-account",
    type=str,
    default=None,
    help="GCP service account email for GKE Workload Identity (e.g., app-sa@project.iam.gserviceaccount.com).",
)
def deploy(
    env: str,
    tag: str | None,
    api_image_repo: str,
    worker_image_repo: str | None,
    skip_db_wait: bool,
    skip_redis_wait: bool,
    skip_rollout_wait: bool,
    env_file: str,
    scratch_path: str | None,
    gcp_service_account: str | None,
) -> None:
    """Deploys the application to the specified environment."""
    check_kubectl()

    # Load and validate environment
    console.print(f"[cyan]Loading environment variables from [bold]{env_file}[/bold]...[/cyan]")
    load_dotenv(env_file)
    missing = [key for key in REQUIRED_SECRETS if key not in os.environ]
    if missing:
        console.print(f"[bold red]Error: Missing required secrets: {', '.join(missing)}[/bold red]")
        sys.exit(1)

    console.print(Panel(f"🚀 Starting Deployment to [bold cyan]{env}[/bold cyan] Environment 🚀", expand=False))

    # Build configuration
    config = build_deploy_config(env, api_image_repo, worker_image_repo, tag, gcp_service_account, scratch_path)
    namespace = config["namespace"]

    # Ensure namespace exists
    console.print(f"[cyan]Ensuring namespace '{namespace}' exists...[/cyan]")
    run_kubectl(["create", "namespace", namespace], check=False)

    # Apply all manifests
    apply_all_manifests(config)

    # Wait for infrastructure
    if not skip_db_wait:
        wait_for_pod(namespace, "postgres", "300s", "Database")
    if not skip_redis_wait:
        wait_for_pod(namespace, "redis", "120s", "Redis")
    if not skip_rollout_wait:
        wait_for_deployments(namespace, ["api", "worker", "web"])

    console.print(
        Panel(f"✅ [bold green]{env.capitalize()} Deployment Completed Successfully![/bold green] ✅", expand=False)
    )
    show_deployment_status(namespace, config.get("ingress_enabled", False))


# --- Delete Command ---
@cli.command()
@click.option(
    "-e",
    "--env",
    type=click.Choice(["dev", "prod"]),
    required=True,
    help="Deployment environment to delete resources from.",
)
@click.option(
    "--delete-namespace", is_flag=True, default=False, help="Also delete the entire namespace (USE WITH CAUTION)."
)
@click.option("--delete-pvc", is_flag=True, default=False, help="Also delete the PersistentVolumeClaims (DATA LOSS).")
@click.option(
    "--api-image-repo",
    type=str,
    default="your-repo/litestar-app",
    help="Docker image repository for API (for context).",
)
@click.option(
    "--worker-image-repo",
    type=str,
    default=None,
    help="Docker image repository for worker (defaults to api-image-repo).",
)
@click.option(
    "--env-file",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=str),
    required=True,
    help="Path to a .env file to load secrets/config from (using python-dotenv).",
)
@click.option(
    "--scratch-path",
    type=str,
    default=None,
    help="Optional: Enable a scratch volume and mount it at this path (e.g. /tmp/app).",
)
def delete(
    env: str,
    delete_namespace: bool,
    delete_pvc: bool,
    api_image_repo: str,
    worker_image_repo: str | None,
    env_file: str,
    scratch_path: str | None,
) -> None:
    """Deletes application resources from the specified environment."""
    check_kubectl()
    console.print(f"[cyan]Loading environment variables from [bold]{env_file}[/bold]...[/cyan]")
    load_dotenv(env_file)
    # Validate required secrets (for delete, warn if missing but do not exit)
    missing = [key for key in REQUIRED_SECRETS if key not in os.environ]
    if missing:
        console.print(
            f"[yellow]Warning: The following required secrets are missing from the .env file: {', '.join(missing)}. Some deletions may not work as expected.[/yellow]"
        )
    console.print(Panel(f"🗑️ Starting Deletion for [bold yellow]{env}[/bold yellow] Environment 🗑️", expand=False))
    config = CONFIG[env].copy()

    # Image configuration
    config["api_image_repo"] = api_image_repo
    config["worker_image_repo"] = worker_image_repo or api_image_repo
    config["image_repo"] = api_image_repo  # Legacy compatibility
    config["image_tag"] = "delete-context"  # Placeholder

    # Secrets (use placeholders if not available - only needed for template rendering)
    db_password = os.environ.get("DATABASE_PASSWORD", "placeholder")
    secret_key = os.environ.get("SECRET_KEY", "placeholder")
    config["database_password_b64"] = base64.b64encode(db_password.encode()).decode()
    config["secret_key_b64"] = base64.b64encode(secret_key.encode()).decode()

    # Database URL placeholder for template rendering
    db_url = f"postgresql+asyncpg://{config['db_user']}:{db_password}@{config['db_host']}:{config['db_port']}/{config['db_name']}"
    config["database_url_b64"] = base64.b64encode(db_url.encode()).decode()

    # Set APP_SCRATCH_PATH in context if provided
    if scratch_path:
        config["APP_SCRATCH_PATH"] = scratch_path
    elif config.get("app_scratch_path"):
        config["APP_SCRATCH_PATH"] = config["app_scratch_path"]
    # else: do not set, so the template disables the feature

    namespace = config["namespace"]

    # 1. Render and Delete manifests in reverse order
    console.print(f"[yellow]Deleting resources in namespace {namespace}...[/yellow]")
    for template_name in TEMPLATES_DELETE_ORDER:
        # Skip ingress if not enabled for the environment
        if template_name == "ingress.yaml.j2" and not config.get("ingress_enabled", False):
            continue
        # Skip PVC unless explicitly requested
        if template_name == "db-pvc.yaml.j2" and not delete_pvc:
            console.print(
                f"[yellow dim]Skipping PVC deletion for {template_name}. Use --delete-pvc to include.[/yellow dim]"
            )
            continue

        console.print(f"\n[yellow]Processing template for deletion:[/yellow] {template_name}")
        try:
            # Render template to get resource kinds/names if needed, but primarily delete by file
            rendered_yaml = render_template(template_name, config)
            delete_manifest(rendered_yaml, namespace)
        except Exception as e:
            console.print(f"[red]Error processing {template_name} for deletion: {e}. Continuing...[/red]")

    # 2. Optionally delete Namespace
    if delete_namespace:
        if env == "prod" and not click.confirm(
            f"\n[bold red]🚨 EXTREME CAUTION 🚨 Are you sure you want to delete the ENTIRE production namespace '{namespace}'? This is IRREVERSIBLE.",
            abort=True,
        ):
            pass  # Should be unreachable due to abort=True

        console.print(f"\n[bold red]Deleting namespace '{namespace}'...[/bold red]")
        run_kubectl(["delete", "namespace", namespace, "--ignore-not-found=true"], check=False)
    else:
        console.print(f"\n[yellow]Namespace '{namespace}' not deleted. Use --delete-namespace to remove it.[/yellow]")

    if not delete_pvc:
        console.print(
            "[yellow]PersistentVolumeClaim 'postgres-pvc' may still exist. Use --delete-pvc during delete to remove it (DATA LOSS).[/yellow]"
        )

    console.print(Panel(f"✅ [bold green]{env.capitalize()} Deletion Process Completed.[/bold green] ✅", expand=False))


def b64encode_filter(s: str) -> str:
    """Jinja filter to base64 encode a string.

    Args:
        s: The string to base64 encode.

    Returns:
        The base64 encoded string.
    """
    return base64.b64encode(s.encode()).decode()


if __name__ == "__main__":
    # Add base64 filter to Jinja
    jinja_env.filters["b64encode"] = b64encode_filter
    cli()
