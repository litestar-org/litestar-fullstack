from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

REDIRECT_TEMPLATE = """
<!DOCTYPE HTML>
<html lang="en-US">
    <head>
        <title>Page Redirection</title>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="0; url={target}">
        <script type="text/javascript">window.location.href = "{target}"</script>
    </head>
    <body>
        You are being redirected. If this does not work, click <a href='{target}'>this link</a>
    </body>
</html>
"""

parser = argparse.ArgumentParser()
parser.add_argument("output")


def build(output_dir: str) -> None:
    target = _resolve_output_dir(output_dir)
    subprocess.run(["make", "docs"], check=True)  # noqa: S607

    target.mkdir()
    target.joinpath(".nojekyll").touch(exist_ok=True)
    target.joinpath("index.html").write_text(REDIRECT_TEMPLATE.format(target="latest"))

    docs_src_path = Path("docs/_build/html")
    shutil.copytree(docs_src_path, target / "latest", dirs_exist_ok=True)


def main() -> None:
    args = parser.parse_args()
    build(output_dir=args.output)


def _resolve_output_dir(output_dir: str) -> Path:
    root = Path.cwd().resolve()
    target = (root / output_dir).resolve()
    if target == root or not target.is_relative_to(root):
        msg = f"Output directory must be a subdirectory of {root}"
        raise SystemExit(msg)
    return target


if __name__ == "__main__":
    main()
