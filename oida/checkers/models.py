import ast
from contextlib import contextmanager
from functools import reduce
from typing import Any, Iterator

from ..config import ComponentConfig, ProjectConfig
from .base import Checker, Code

RELATED_FIELD_CLASSES = (
    "django.db.models.ForeignKey",
    "django.db.models.OneToOneField",
    "tienda.core.fields.OneToOneOrNoneField",
)


class ComponentModelIsolationChecker(Checker):
    """
    TODO: classdoc
    """

    slug = "component-model-isolation"

    def __init__(
        self,
        module: str | None,
        name: str,
        component_config: ComponentConfig | None,
        project_config: ProjectConfig,
    ) -> None:
        super().__init__(module, name, component_config, project_config)
        self.scopes: list[dict[str, str]] = [{}]
        # This checker will collect any relations it sees, regardless of any
        # config. This is used to automatically generate component configs with
        # allowed relations based on current violations.
        self.seen_relations: set[str] = set()

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

    def is_violation_silenced(self, path: str) -> bool:
        """Check if a relation that's a violation is ignored by component config"""
        allowed_foreign_keys: tuple[str, ...] = (
            getattr(self.component_config, "allowed_foreign_keys", None) or ()
        )

        if path in allowed_foreign_keys:
            return True

        return False

    def maybe_report_violation(self, *, field_path: str, node: ast.AST) -> None:
        """Check a fully qualified name"""

        # If access is not allowed we should record the reference even if the
        # violation is silenced
        self.seen_relations.add(field_path)

        if self.is_violation_silenced(field_path):
            return

        self.report_violation(
            node, Code.ODA006, f"Related field to a different app: {field_path}"
        )

    def visit_Module(self, node: ast.Module) -> None:
        """Only check the file if the module is not ignored"""

        if not self.project_config.is_ignored(self.module, self.name):
            super().generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level > 0 or not self.module or not node.module:
            return

        for name in node.names:
            self.current_scope[
                name.asname if name.asname else name.name
            ] = f"{node.module}.{name.name}"

    def visit_Import(self, node: ast.Import) -> Any:

        # Ignore files that are not in a module
        if self.module is None:
            return

        for name in node.names:
            top_name, *_ = name.name.split(".", 1)

            if name.asname:
                self.current_scope[name.asname] = name.name
            else:
                # `import foo.bar` only sets foo in the local scope
                self.current_scope[top_name] = top_name

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        with self.push_scope():
            self.generic_visit(node)

    def generic_visit(self, node):
        # print('generic_visit', node, node.__dict__)
        return super().generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:

        with self.push_scope():
            self.current_scope["assign_target"] = getattr(node.targets[0], "id", None)
            self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func

        if not isinstance(func, ast.Attribute | ast.Name):
            return

        func_path = self.resolve_node_fullpath(func)

        if func_path not in RELATED_FIELD_CLASSES:
            return self.generic_visit(node)

        field_path = (
            f"{self.scope.get('current_class')}.{self.scope.get('assign_target')}"
        )

        # Related fields are usually the first arg, but can also be passed as the "to" kwarg
        related_model_node = None
        if node.args:
            related_model_node = node.args[0]
        elif node.keywords:
            to_keyword = next((kw for kw in node.keywords if kw.arg == "to"), None)
            related_model_node = to_keyword.value

        if isinstance(related_model_node, ast.Constant):
            # We don't really know which app we currently are in, as it might not be named
            # the same as the folder, and we might have different depths of apps in different
            # contexts. E.g. if the project is componentized or not.

            # TODO: This assumed app name based on the path
            module_app = self.module.split(".")[1]
            import_app = related_model_node.value.split(".")[0]

        elif isinstance(related_model_node, ast.Attribute | ast.Name):
            related_path = self.resolve_node_fullpath(related_model_node)

            module_app = ".".join(self.module.split(".")[:2])
            import_app = ".".join(related_path.split(".")[:2])

        else:
            print("WARNING")
            return

        if self.is_same_app(module_app, import_app):
            # print("same app", self.module, field_path)
            pass
        else:
            self.maybe_report_violation(field_path=field_path, node=node)

    def resolve_node_fullpath(self, node: ast.Attribute | ast.Name) -> str:
        """
        Takes in an ast expression, and tries to resolve the full name of the reference.
        Currently only works for ast.Attribute and ast.Name.
        """

        parts = []

        while isinstance(node, ast.Attribute):
            parts.insert(0, node.attr)
            node = node.value

        if isinstance(node, ast.Name):
            parts.insert(0, self.scope.get(node.id))

        return ".".join([part for part in parts if part is not None])

    def visit_ClassDef(self, node):
        self.current_scope[node.name] = self.module
        with self.push_scope():
            self.current_scope["current_class"] = node.name
            self.generic_visit(node)
