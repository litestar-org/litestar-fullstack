#!/usr/bin/env -S uv run python
# ruff: noqa: S404, BLE001, FIX002
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

BASE_DIR = Path(__file__).parent
TEMPLATE_DIR = BASE_DIR / "templates"
KUBECTL_CMD = "kubectl"

# Define environment-specific configurations
# TODO: Add/adjust values based on your needs
CONFIG: dict[str, dict[str, Any]] = {
    "dev": {
        "namespace": "litestar-dev",
        "image_tag": "latest",
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
        "db_storage": "5Gi",
        "log_level": "DEBUG",
        "allowed_cors_origins": '["*"]',
        "api_workers": 1,
        "saq_concurrency": 10,
        "hpa_cpu_target": 70,
        "hpa_mem_target": None,  # No memory target for dev HPA
        "ingress_enabled": False,
        "ingress_host": None,
        "ingress_tls_secret": None,
        "cert_issuer": None,
        "app_scratch_path": None,  # Optional scratch path for dev
    },
    "prod": {
        "namespace": "litestar-prod",
        "image_tag": "latest",  # Should be overridden with a specific tag for prod deploys
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
        "db_storage": "20Gi",  # More storage for prod
        "log_level": "INFO",
        "allowed_cors_origins": '["https://your-frontend-domain.com"]',  # IMPORTANT: Change this!
        "api_workers": 4,  # Adjust based on prod instance size/cores
        "saq_concurrency": 20,  # Adjust based on expected load
        "hpa_cpu_target": 60,  # Lower target for better responsiveness
        "hpa_mem_target": 75,  # Add memory scaling for prod
        "ingress_enabled": True,
        "ingress_host": "your-domain.com",  # IMPORTANT: Change this!
        "ingress_tls_secret": "your-domain-tls",  # cert-manager creates this
        "cert_issuer": "letsencrypt-prod",  # Adjust if needed
        "app_scratch_path": None,  # Optional scratch path for prod
    },
}

# Templates to render and apply (in order)
TEMPLATES_APPLY_ORDER = [
    "namespace.yaml.j2",
    "secrets.yaml.j2",
    "configmap.yaml.j2",
    "db-pvc.yaml.j2",
    "db-service.yaml.j2",
    "db-statefulset.yaml.j2",
    "api-service.yaml.j2",
    "web-service.yaml.j2",
    "nginx-config.yaml.j2",  # Nginx config needs to exist before deployment
    "api-deployment.yaml.j2",
    "worker-deployment.yaml.j2",
    "web-deployment.yaml.j2",
    "api-hpa.yaml.j2",
    "worker-hpa.yaml.j2",
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
  python deploy.py deploy -e dev --env-file .env

  [dim]# Deploy to production[/dim]
  python deploy.py deploy -e prod --tag v1.2.3 --env-file .env

  [dim]# Deploy with a scratch path[/dim]
  python deploy.py deploy -e dev --env-file .env --scratch-path /tmp/app

  [dim]# Delete all resources from dev[/dim]
  python deploy.py delete -e dev --env-file .env

  [dim]# Delete all resources and the namespace from prod[/dim]
  python deploy.py delete -e prod --delete-namespace --delete-pvc --env-file .env

[bold]REQUIRED:[/bold]
  --env-file         Path to a .env file containing all required secrets and configuration.

[bold]REQUIRED SECRETS IN .env:[/bold]
  SECRET_KEY       The application secret key (will be base64 encoded in the secret).
  DATABASE_PASSWORD The database password (will be base64 encoded in the secret).

[bold]NOTES:[/bold]
- All secrets and sensitive configuration must be provided via the [bold]--env-file[/bold] option (using a .env file, see [dim]python-dotenv[/dim]).
- You may use [bold]--scratch-path[/bold] to enable a scratch volume at the given path (see templates).
- You must have [bold]kubectl[/bold] installed and configured.
- For production, always use a specific image tag (not 'latest').
- The tool will prompt for confirmation before deleting a production namespace.
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
@click.option("--image-repo", type=str, default="your-repo/litestar-app", help="Docker image repository.")
@click.option("--skip-db-wait", is_flag=True, default=False, help="Skip waiting for the database pod to be ready.")
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
def deploy(
    env: str,
    tag: str | None,
    image_repo: str,
    skip_db_wait: bool,
    skip_rollout_wait: bool,
    env_file: str,
    scratch_path: str | None,
) -> None:
    """Deploys the application to the specified environment."""
    check_kubectl()
    console.print(f"[cyan]Loading environment variables from [bold]{env_file}[/bold]...[/cyan]")
    load_dotenv(env_file)
    # Validate required secrets
    missing = [key for key in REQUIRED_SECRETS if key not in os.environ]
    if missing:
        console.print(
            f"[bold red]Error: The following required secrets are missing from the .env file: {', '.join(missing)}[/bold red]"
        )
        sys.exit(1)
    console.print(Panel(f"🚀 Starting Deployment to [bold cyan]{env}[/bold cyan] Environment 🚀", expand=False))
    config = CONFIG[env].copy()
    config["image_repo"] = image_repo
    if tag:
        config["image_tag"] = tag
        console.print(f"[yellow]Using provided image tag:[/yellow] {tag}")
    elif env == "prod":
        console.print("[bold red]Error: --tag is required for production deployments.[/bold red]")
        sys.exit(1)
    else:
        console.print(f"[yellow]Using default image tag for {env}:[/yellow] {config['image_tag']}")
    # Use only values from .env for secrets
    config["secret_key_b64"] = base64.b64encode(os.environ["SECRET_KEY"].encode()).decode()
    config["database_password_b64"] = base64.b64encode(os.environ["DATABASE_PASSWORD"].encode()).decode()

    # Set APP_SCRATCH_PATH in context if provided
    if scratch_path:
        config["APP_SCRATCH_PATH"] = scratch_path
    elif config.get("app_scratch_path"):
        config["APP_SCRATCH_PATH"] = config["app_scratch_path"]
    # else: do not set, so the template disables the feature

    namespace = config["namespace"]

    # 1. Ensure Namespace exists
    console.print(f"[cyan]Ensuring namespace '{namespace}' exists...[/cyan]")
    run_kubectl(["create", "namespace", namespace], check=False)  # Ignore error if it already exists

    # 2. Render and Apply manifests in order
    console.print(f"[cyan]Applying manifests for {env}...[/cyan]")
    for template_name in TEMPLATES_APPLY_ORDER:
        # Skip ingress if not enabled for the environment
        if template_name == "ingress.yaml.j2" and not config.get("ingress_enabled", False):
            continue

        console.print(f"\n[green]Processing template:[/green] {template_name}")
        rendered_yaml = render_template(template_name, config)
        # console.print("[dim]--- Rendered YAML ---")
        # console.print(f"{rendered_yaml}[/dim]")
        # console.print("[dim]---------------------[/dim]")
        apply_manifest(rendered_yaml, namespace)

    # 3. Wait for Deployments (Optional)
    if not skip_db_wait:
        console.print(f"\n[cyan]Waiting for database pod in namespace '{namespace}'...[/cyan]")
        try:
            run_kubectl([
                "wait",
                "--for=condition=ready",
                "pod",
                "-l",
                "app=postgres",
                "-n",
                namespace,
                "--timeout=300s",
            ])
            console.print("[green]Database pod is ready.[/green]")
        except subprocess.CalledProcessError:
            console.print(
                "[yellow]Warning: Database pod readiness check timed out or failed. Check pod status manually.[/yellow]"
            )

    if not skip_rollout_wait:
        deployments_to_check = ["api", "worker", "web"]
        for deployment_name in deployments_to_check:
            console.print(f"\n[cyan]Waiting for rollout status of deployment '{deployment_name}'...[/cyan]")
            try:
                run_kubectl(["rollout", "status", f"deployment/{deployment_name}", "-n", namespace, "--timeout=300s"])
                console.print(f"[green]Deployment '{deployment_name}' rollout complete.[/green]")
            except subprocess.CalledProcessError:
                console.print(
                    f"[yellow]Warning: Rollout status check for deployment '{deployment_name}' timed out or failed.[/yellow]"
                )

    console.print(
        Panel(f"✅ [bold green]{env.capitalize()} Deployment Completed Successfully![/bold green] ✅", expand=False)
    )

    # 4. Show Status (Optional)
    console.print("\n[blue]--- Current Status ---[/blue]")
    run_kubectl(["get", "pods", "-n", namespace], check=False)
    run_kubectl(["get", "svc", "-n", namespace], check=False)
    if config.get("ingress_enabled", False):
        run_kubectl(["get", "ingress", "-n", namespace], check=False)
    console.print("[blue]--------------------[/blue]")


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
@click.option("--delete-pvc", is_flag=True, default=False, help="Also delete the PersistentVolumeClaim (DATA LOSS).")
@click.option(
    "--image-repo", type=str, default="your-repo/litestar-app", help="Docker image repository (needed for context)."
)  # Needed for context rendering
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
    image_repo: str,
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
    config["image_repo"] = image_repo
    config["image_tag"] = "delete-context"  # Placeholder
    db_password = os.environ.get("DATABASE_PASSWORD", "placeholder")
    secret_key = os.environ.get("SECRET_KEY", "placeholder")
    config["database_password_b64"] = base64.b64encode(db_password.encode()).decode() if db_password else "placeholder"
    config["secret_key_b64"] = base64.b64encode(secret_key.encode()).decode() if secret_key else "placeholder"

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
