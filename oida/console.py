import argparse
import sys
from pathlib import Path

from oida.statistics.statistics_generator import generate_statistics

from .checkers import get_checkers
from .commands import componentize_app, generate_config, run_linter


def main() -> None:

    parser = argparse.ArgumentParser(description="Django project linter.")

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    lint_parser = subparsers.add_parser("lint", help="Run linting on a project")
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

    config_parser = subparsers.add_parser(
        "config",
        help="Generate component config files that whitelist all isolation violations",
    )
    config_parser.add_argument(
        "project_root", type=Path, help="Path to project root directory"
    )

    config_parser = subparsers.add_parser(
        "statistics",
        help="Generate statistics about the modularization state",
    )
    config_parser.add_argument(
        "project_root", type=Path, help="Path to project root directory"
    )

    componentize_parser = subparsers.add_parser(
        "componentize",
        help=componentize_app.__doc__,
    )
    componentize_parser.add_argument("old_path", type=Path, help="Current path to app")
    componentize_parser.add_argument("new_path", type=Path, help="Path to move app to")

    args = parser.parse_args()

    if args.command == "lint":
        has_violations = run_linter(*args.paths, checks=args.checks)
        if has_violations:
            sys.exit(1)
    elif args.command == "config":
        generate_config(args.project_root)
    elif args.command == "statistics":
        statistics = generate_statistics(args.project_root)
        print(f"{statistics.json()}")
    elif args.command == "componentize":
        componentize_app(args.old_path, args.new_path)
    else:
        sys.exit(f"Unknown command: {args.command}")
