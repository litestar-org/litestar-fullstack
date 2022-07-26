import sys


def main() -> None:
    try:
        from pyspa.cli import cli
    except ImportError:
        print(  # noqa: T201
            "💣 [bold red] Could not load required libraries.  ",
            "Please check your installation",
        )
        sys.exit(1)
    cli()


if __name__ == "__main__":
    main()
