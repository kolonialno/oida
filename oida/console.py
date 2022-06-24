import argparse
import sys
from pathlib import Path

from .checkers import get_checkers
from .commands import run_linter


def main() -> None:

    parser = argparse.ArgumentParser(description="Django project linter.")

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    lint_parser = subparsers.add_parser("lint", help="Run linting on a projec")
    lint_parser.add_argument(
        "paths",
        metavar="path",
        type=Path,
        nargs="+",
        help="One or more paths to check",
    )
    lint_parser.add_argument(
        "--check",
        dest="checks",
        action="append",
        help="Specify checks to run",
        choices=[checker_cls.slug for checker_cls in get_checkers()],
    )

    args = parser.parse_args()

    if args.command == "lint":
        if not run_linter(*args.paths, checks=args.checks):
            sys.exit(1)
    else:
        sys.exit(f"Unknown command: {args.command}")
