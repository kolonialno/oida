import ast
from typing import cast

from ..config import Config
from .base import Checker


class CheckConfig(Checker):
    """
    This checker reports violations in the confcomponent.py files.
    """

    slug = "config"

    def __init__(self, module: str, name: str) -> None:
        super().__init__(module, name)
        self.config = Config()

    def visit_Module(self, node: ast.Module) -> None:

        # This checker only looks at confcomponent.py files
        if self.name != "confcomponent":
            return

        for statement in node.body:
            if isinstance(statement, ast.AnnAssign):
                self.visit_AnnAssign(statement)
            elif isinstance(statement, ast.Assign):
                self.visit_Assign(statement)
            else:
                self.report_violation(
                    statement,
                    "Component config files should only contain assignment statements",
                )

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        target = node.target
        if not isinstance(target, ast.Name):
            return self.report_violation(node, "Unknown expression in component config")

        return self.check_assign(target.id, node)

    def visit_Assign(self, node: ast.Assign) -> None:
        match node:
            case ast.Assign(targets=[ast.Name() as target]):
                self.check_assign(target.id, node)
            case _:
                self.report_violation(node, "Unknown expression in component config")

    def check_assign(self, name: str, node: ast.AnnAssign | ast.Assign) -> None:

        if name == "ALLOWED_IMPORTS":
            return self.check_allowed_imports(node)

        self.report_violation(
            node, f'Unknown constant "{name}" assigned in component config'
        )

    def check_allowed_imports(self, node: ast.AnnAssign | ast.Assign) -> None:
        """
        Check thhe
        """

        # Silently ignore type-only assignments: ALLOWED_IMPORTS: tuple[str, ...]
        if node.value is None:
            return

        if not isinstance(node.value, ast.Tuple):
            return self.report_violation(
                node.value,
                "ALLOWED_IMPORTS should be a tuple of string literals",
            )

        if not all(
            isinstance(item, ast.Constant) and isinstance(item.value, str)
            for item in node.value.elts
        ):
            return self.report_violation(
                node.value, "ALLOWED_IMPORTS should be a tuple of string literals"
            )

        self.config.allowed_imports = tuple(
            cast(ast.Constant, item).value for item in node.value.elts
        )
