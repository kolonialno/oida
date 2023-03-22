"""
This defines a flake8 plugin, so Oida can be run through flake8.
"""

import ast
from importlib.metadata import version
from pathlib import Path
from typing import Any, Generator, Type

from .checkers import get_checkers
from .discovery import get_component_config, get_module, get_project_config


class Plugin:
    name = "oida"
    version = version("oida")

    def __init__(self, tree: ast.AST, filename: str) -> None:
        self._tree = tree

        # Figure out the name of the current package (if the file is in one)
        path = Path(filename)
        self._module = get_module(path.parent)
        self._name = "" if path.name == "__init__.py" else path.stem
        self._component_config = get_component_config(path.parent)
        self._project_config = get_project_config(path.parent)

    def run(self) -> Generator[tuple[int, int, str, Type[Any]], None, None]:
        for checker_cls in get_checkers():
            checker = checker_cls(
                self._module, self._name, self._component_config, self._project_config
            )
            checker.visit(self._tree)
            for line, col, code, message in checker.violations:
                yield line, col, f"ODA{code.value:03d} {message}", type(self)
