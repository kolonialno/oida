from pathlib import Path

from .checkers import get_checkers
from .discovery import find_modules
from .reporter import StdoutReporter


def run(*paths: Path) -> bool:
    reporter = StdoutReporter()
    checkers = get_checkers()
    for module in find_modules(paths):
        # print(f"Checking {module.name} ({module.path})")
        for checker in checkers:
            checker.check(module, reporter)
        # Clear ast from memory as we no longer need it
        del module.ast

    reporter.print_summary()
    return reporter.has_violations
