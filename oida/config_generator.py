import ast
from pathlib import Path

from .checkers import ComponentIsolationChecker
from .discovery import get_module


def collect_violations(project_root: Path) -> dict[Path, set[str]]:
    """
    Collect violations in components. Returns a dictionary mapping from
    component path to a set of violations.
    """

    violations: dict[Path, set[str]] = {}

    for path in project_root.iterdir():
        if path.is_dir() and (path / "__init__.py").exists():
            violations[path] = collect_violations_in_dir(path)

    return violations


def collect_violations_in_dir(path: Path) -> set[str]:
    """
    Recursively collect all violations in a directory.
    """

    violations: set[str] = set()
    for child in path.iterdir():
        if child.is_dir():
            if (child / "__init__.py").exists():
                violations |= collect_violations_in_dir(child)
        elif child.suffix == ".py":
            violations |= collect_violations_in_file(child)

    return violations


def collect_violations_in_file(path: Path) -> set[str]:
    """
    Collect all violations in the given Python file.
    """

    module = get_module(path)
    checker = ComponentIsolationChecker(module, path.stem, None)
    with open(path) as f:
        checker.visit(ast.parse(f.read(), str(path)))
    return checker.referenced_imports
