from pathlib import Path
from typing import Literal

from .checkers import get_checkers
from .config import SubserviceConfig
from .discovery import find_modules
from .reporter import StdoutReporter


def run(
    *paths: Path, output_format: Literal["default", "github"], checks: list[str]
) -> bool:
    reporter = StdoutReporter()
    checkers = [checker for checker in get_checkers() if checker.name in checks]
    config: dict[str, SubserviceConfig] | None = None
    for module in find_modules(paths):
        for checker in checkers:
            if result := checker.check(module, reporter, config):
                config = result
        # Clear ast from memory as we no longer need it
        del module.ast

    reporter.print_summary()
    return reporter.has_violations
