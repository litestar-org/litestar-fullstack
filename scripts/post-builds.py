from __future__ import annotations

import argparse
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

PYAPP_VERSION = "v0.14.0"
PYAPP_URL = f"https://github.com/ofek/pyapp/releases/download/{PYAPP_VERSION}/source.tar.gz"
PROJECT_ROOT = Path(__file__).parent.parent
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)8s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("post-build")


def package_standalone_app(options: argparse.Namespace) -> None:
    subprocess.run(
        ["/usr/bin/env", "uv", "export", "--no-hashes", "--no-dev", "--output-file", "dist/requirements.txt"],
        check=False,
    )
    with Path(PROJECT_ROOT / "dist/requirements.txt").open("+a") as f:
        f.writelines([str(os.fspath(Path(options.wheel_file).absolute()))])
    logger.info("PYAPP_PROJECT_PATH is set to %s", os.fspath(Path(options.wheel_file).absolute()))
    pyapp_configuration = {
        "PYAPP_PROJECT_PATH": str(Path(options.wheel_file).absolute()),
        # "PYAPP_PROJECT_DEPENDENCY_FILE": str(Path(PROJECT_ROOT / "dist/requirements.txt").absolute()),
        # "PYAPP_PROJECT_NAME": "app",
        # "PYAPP_PROJECT_VERSION": "0.2.0",
        # "PYAPP_EXEC_MODULE": "app",
        "PYAPP_PYTHON_VERSION": "3.11",
        # "PYAPP_DISTRIBUTION_EMBED": "1",
        "PYAPP_FULL_ISOLATION": "1",
        "PYAPP_EXEC_SPEC": "app.__main__:run_cli",
        "PYAPP_PIP_EXTRA_ARGS": "--only-binary :all:",
        "RUST_BACKTRACE": "full",
        "CARGO_PROFILE_RELEASE_BUILD_OVERRIDE_DEBUG": "true",
        "PATH": os.environ["PATH"],
    }
    for env_var, val in pyapp_configuration.items():
        os.environ[env_var] = val
    logger.info("Setting the following environment variables %s", pyapp_configuration)

    with tempfile.TemporaryDirectory() as app_temp_dir:
        subprocess.run(["/usr/bin/env", "wget", PYAPP_URL, "-O", f"{app_temp_dir}/pyapp.tar.gz"], check=False)
        subprocess.run(
            [
                "/usr/bin/env",
                "tar",
                "-xvf",
                f"{app_temp_dir}/pyapp.tar.gz",
                "-C",
                app_temp_dir,
                "--strip-components",
                "1",
            ],
            check=True,
        )

        subprocess.run(
            [
                "/usr/bin/env",
                "cargo",
                "build",
                "--release",
            ],
            check=False,
            cwd=app_temp_dir,
            # env=pyapp_configuration,
        )
        # subprocess.run(
        #     [
        #         "/usr/bin/env",
        #         "cargo",
        #         "install",
        #         "--path",
        #         app_temp_dir,
        #         # "--git",
        #         # "https://github.com/ofek/pyapp",
        #         # "--tag",
        #         # PYAPP_VERSION,
        #         "--force",
        #         "--root",
        #         app_temp_dir,
        #     ],
        #     env=pyapp_configuration,
        #     check=True,
        # )

        for suffix in ["", ".exe"]:
            from_path = Path(app_temp_dir, "bin", "pyapp").with_suffix(suffix)
            if not from_path.exists():
                continue

            to_path = Path(options.out_dir, options.name).with_suffix(suffix)
            to_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(from_path, to_path)

            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Manage Package Post-Build Processes")
    parser.add_argument("--wheel-file", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--name", required=True, default="app")
    args = parser.parse_args()
    package_standalone_app(args)
