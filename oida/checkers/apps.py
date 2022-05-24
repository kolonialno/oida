import ast
from contextlib import contextmanager
from functools import reduce
from typing import Iterator

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

    slug = "app-isolation"

    def __init__(self, module: str, name: str) -> None:
        super().__init__(module, name)
        self.scopes: list[dict[str, str]] = [{}]

    @property
    def current_scope(self) -> dict[str, str]:
        return self.scopes[-1]

    @property
    def in_scope(self) -> dict[str, str]:
        return reduce(dict.__or__, self.scopes)

    @contextmanager
    def push_scope(self) -> Iterator[None]:
        self.scopes.append({})
        try:
            yield
        finally:
            self.scopes.pop()

    def is_same_app(self, app_a: str, app_b: str) -> bool:
        if app_a == app_b:
            return True

        return False

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level > 0 or not self.module or not node.module:
            return

        module = self.module.split(".")
        components = node.module.split(".")

        # Ignore imports from third party libraries
        if components[0] != module[0]:
            return

        module_app = ".".join(module[:2])
        import_app = ".".join(components[:2])

        # Ignore imports within the same sub-service
        if self.is_same_app(module_app, import_app):
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
                self.current_scope[
                    name.asname if name.asname else name.name
                ] = f"{node.module}.{name.name}"

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        with self.push_scope():
            self.generic_visit(node)

    def visit_arg(self, node: ast.arg) -> None:
        """Implemented to avoid visit_Name being called for annotations"""

        # TODO: Need to check the value bit

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Implemented to avoid visit_Name being called for annotations"""

        # TODO: Need to check the non-name side of things

    def visit_Name(self, node: ast.Name) -> None:
        scope = self.in_scope
        if node.id in scope:
            self.report_violation(
                node, f'Private variable "{scope[node.id]}" referenced'
            )
