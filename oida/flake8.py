"""
This defines a flake8 plugin, so Oida can be run through flake8.
"""

import ast
from importlib.metadata import version
from pathlib import Path
from typing import Any, Generator, Type

from .checkers import RelativeImportsChecker
from .discovery import get_module


class Plugin:
    name = "oida"
    version = version("oida")

    def __init__(self, tree: ast.AST, filename: str) -> None:
        self._tree = tree

        # Figure out the name of the current package (if the file is in one)
        path = Path(filename)
        self._module = get_module(path.parent)
        self._name = "" if path.name == "__init__.py" else path.stem

    def run(self) -> Generator[tuple[int, int, str, Type[Any]], None, None]:
        checker = RelativeImportsChecker(self._module, self._name)
        checker.visit(self._tree)
        for line, col, message in checker.violations:
            yield line, col, message, type(self)
