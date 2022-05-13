import argparse
import sys
from pathlib import Path

from . import checkers
from .runner import run


def main() -> None:
    check_names = [getattr(checkers, name).name for name in checkers.__all__]

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
        choices=check_names,
    )
    parser.add_argument(
        "--format",
        help="Choose the output format to use",
        default="default",
        choices=["default", "github"],
    )

    args = parser.parse_args()

    checks = args.checks if args.checks else check_names

    if not run(*args.paths, output_format=args.format, checks=checks):
        sys.exit(1)
