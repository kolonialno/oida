from pathlib import Path

from .checkers import get_checkers
from .discovery import find_modules


def run(*paths: Path) -> None:
    checkers = get_checkers()
    for module in find_modules(paths):
        # print(f"Checking {module.name} ({module.path})")
        for checker in checkers:
            checker.check(module)
        # Clear ast from memory as we no longer need it
        del module.ast
