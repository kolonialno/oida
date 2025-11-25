from pathlib import Path

from ..checkers import Code, get_checkers
from ..discovery import find_modules, get_component_config, get_project_config


def print_violation(
    file: Path, line: int, column: int, code: Code, message: str
) -> None:
    print(f"{file}:{line}:{column}: {message}")


def run_linter(*paths: Path, checks: list[str]) -> bool:
    has_violations = False
    checkers = get_checkers(checks)
    for module in find_modules(*paths):
        component_config = get_component_config(path=module.path.parent)
        project_config = get_project_config(path=module.path.parent)
        source_lines = module.source_lines
        for checker_cls in checkers:
            checker = checker_cls(
                module=module.module,
                name=module.name,
                component_config=component_config,
                project_config=project_config,
                source_lines=source_lines,
            )
            checker.visit(module.ast)
            if checker.violations:
                has_violations = True
            for violation in checker.violations:
                print_violation(module.path, *violation)
        # Clear ast and source_lines from memory as we no longer need them
        del module.ast
        if hasattr(module, '_source_lines'):
            del module._source_lines

    return has_violations
