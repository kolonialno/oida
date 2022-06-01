import ast
from contextlib import contextmanager
from functools import reduce
from typing import Any, Iterator

from ..config import Config
from .base import Checker


class ComponentIsolationChecker(Checker):
    """
    Check that isolation between components are guaranteed. That means that all
    imports from other components should be from the other component's top
    level. Other imports are allowed for typing purposes.

    Example 1:
        # project/component/app/services.py
        from project.other_component.app.models import Model

        def my_function(model: Model) -> None:  # <-- Allowed
            Model.objects.get()  # <-- Not allowed

    Example 2:
        # project/component/app/services.py
        from project.other_component.services import my_service

        def my_function() -> None:
            my_service()  # <-- This is allowed because it's at the top level
    """

    slug = "component-isolation"

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

    def is_access_allowed(self, full_name: str) -> bool:
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

        # TODO: Check for too deep imports right off the bat, as they might not be accessed

    def visit_Import(self, node: ast.Import) -> Any:
        for name in node.names:
            if name.asname:
                self.current_scope[name.asname] = name.name
            else:
                # `import foo.bar` only sets foo in the local scope
                top_name, *_ = name.name.split(".", 1)
                self.current_scope[top_name] = top_name

        # TODO: Check for too deep imports right off the bat, as they might not be accessed

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
        full_name = self.scope.get(node.id)
        if full_name and not self.is_access_allowed(full_name):
            self.report_violation(node, f'Private attribute "{full_name}" referenced')

    def visit_Attribute(self, node: ast.Attribute) -> Any:

        name = node.attr
        while isinstance(node.value, ast.Attribute):
            # If the attribute starts with an uppercase letter we want to start
            # from the beginning
            if node.value.attr[:1].isupper():
                name = node.value.attr
            else:
                name = f"{node.value.attr}.{name}"
            node = node.value

        # If the attribute chain didn't end in a name we ignore it (ie. a
        # function call or similar)
        if not isinstance(node.value, ast.Name):
            return

        if node.value.id[:1].isupper():
            return self.visit_Name(node.value)

        import_name = self.scope.get(node.value.id)
        if not import_name:
            return

        full_name = f"{import_name}.{name}"

        if not self.is_access_allowed(full_name):
            self.report_violation(node, f'Private attribute "{full_name}" referenced')