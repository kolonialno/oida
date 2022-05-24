from pathlib import Path

from .checkers import get_checkers
from .discovery import find_modules


def print_violation(file: Path, line: int, column: int, message: str) -> None:
    print(f"{file}:{line}:{column}: {message}")


def run(*paths: Path, checks: list[str]) -> bool:
    has_violations = False
    checkers = get_checkers(checks)
    for module in find_modules(paths):
        for checker_cls in checkers:
            checker = checker_cls(module=module.module, name=module.name)
            checker.visit(module.ast)
            if checker.violations:
                has_violations = True
            for violation in checker.violations:
                print_violation(module.path, *violation)
        # Clear ast from memory as we no longer need it
        del module.ast

    return has_violations
