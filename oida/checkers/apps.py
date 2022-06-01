import ast
from contextlib import contextmanager
from functools import reduce
from typing import Iterator

from ..config import Config
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

    def __init__(self, module: str, name: str, component_config: Config | None) -> None:
        super().__init__(module, name, component_config)
        self.scopes: list[dict[str, str]] = [{}]

    @property
    def current_scope(self) -> dict[str, str]:
        return self.scopes[-1]

    @property
    def scope(self) -> dict[str, str]:
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

    def is_import_allowed(self, full_name: str) -> bool:
        allowed_imports: tuple[str, ...] = (
            getattr(self.component_config, "allowed_imports", None) or ()
        )

        # Allow all imports at the root level of a component
        path = full_name.split(".")
        if len(path) == 4:
            return True

        while path:
            if ".".join(path) in allowed_imports:
                return True
            if ".".join(path[:-1]) + ".*" in allowed_imports:
                return True

            path = path[:-1]

        # Name was not found in the list of allowed imports
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

        for name in node.names:
            self.current_scope[
                name.asname if name.asname else name.name
            ] = f"{node.module}.{name.name}"

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        with self.push_scope():
            self.generic_visit(node)

    def visit_arg(self, node: ast.arg) -> None:
        """Implemented to avoid visit_Name being called for annotations"""

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Implemented to avoid visit_Name being called for annotations"""

        self.generic_visit(node.target)
        if node.value:
            self.generic_visit(node.value)

    def visit_Name(self, node: ast.Name) -> None:
        if (name := self.scope.get(node.id)) and not self.is_import_allowed(name):
            self.report_violation(node, f'Private attribute "{name}" referenced')
