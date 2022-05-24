import argparse
import sys
from pathlib import Path

from . import checkers
from .runner import run


def main() -> None:
    checks = [getattr(checkers, name).slug for name in checkers.__all__]

    parser = argparse.ArgumentParser(description="Django project linter.")
    parser.add_argument(
        "paths",
        metavar="path",
        type=Path,
        nargs="+",
        help="One or more paths to check",
    )
    parser.add_argument(
        "--check",
        dest="checks",
        action="append",
        help="Specify checks to run",
        choices=checks,
    )

    args = parser.parse_args()

    if not run(*args.paths, checks=args.checks):
        sys.exit(1)
