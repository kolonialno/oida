import ast
from contextlib import contextmanager
from functools import reduce
from typing import Iterator

from ..module import Module
from ..reporter import Reporter
from .base import Checker


class AppIsolationChecker(Checker):
    """
    Check that for anything imported from another app that's not a service or
    selector it's only used for typing purposes.

    Example:
        # project/app/services.py
        from project.other_app.models import Model

        def my_function(model: Model) -> None:  # <-- Allowed
            Model.objects.get()  # <-- Not allowed
    """

    def check(self, module: Module, reporter: Reporter) -> None:
        self.scopes: list[set[str]] = [set()]
        try:
            super().check(module, reporter)
        finally:
            self.scopes = []

    @property
    def current_scope(self) -> set[str]:
        return self.scopes[-1]

    @property
    def in_scope(self) -> set[str]:
        return reduce(set.__or__, self.scopes)

    @contextmanager
    def push_scope(self) -> Iterator[None]:
        self.scopes.append(set())
        try:
            yield
        finally:
            self.scopes.pop()

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level > 0 or not self.module.package or not node.module:
            return

        module = self.module.package.split(".")
        components = node.module.split(".")

        # Ignore imports from third party libraries
        if components[0] != module[0]:
            return

        # Ignore imports within the same app
        if components[:2] == module[:2]:
            return

        plural = "s" if len(node.names) > 1 else ""

        if "services" in components and components[-1] != "services":
            self.report_violation(
                node, f'Non-public service{plural} imported from "{node.module}"'
            )
        elif "selectors" in components and components[-1] != "selectors":
            self.report_violation(
                node, f'Non-public selector{plural} imported from "{node.module}"'
            )
        elif components[-1] not in ("services", "selectors"):
            for name in node.names:
                self.current_scope.add(name.asname if name.asname else name.name)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        with self.push_scope():
            self.generic_visit(node)

    def visit_arg(self, node: ast.arg) -> None:
        """Implemented to avoid visit_Name being called for annotations"""

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Implemented to avoid visit_Name being called for annotations"""

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in self.in_scope:
            self.report_violation(node, f"Private variable {node.id} referenced")
