import ast

from .base import Checker


class CheckServiceAndSelectorImports(Checker):
    """
    Check that only public services and selectors are imported other apps

    Example:
        # project/my_app/module.py
        from project.other_app.services.private import something # <-- Not allowed
    """

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
        if "selectors" in components and components[-1] != "selectors":
            self.report_violation(
                node, f'Non-public selector{plural} imported from "{node.module}"'
            )


class CheckRelativeImports(Checker):
    """
    Check that no relative imports are extending beyond an app

    Example:
        # project/my_app/module.py
        from ..other_app import models # <-- Not allowed
    """

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level == 0 or not self.module.package:
            return

        path = self.module.package.split(".", 2)
        if len(path) < 2:
            return

        root, app, *_ = path
        absolute_import = self.module.resolve_relative_import(node.module, node.level)

        import_name = "." * node.level + (node.module if node.module else "")

        if not absolute_import.startswith(f"{root}.{app}."):
            self.report_violation(node, f'Relative import outside app: "{import_name}"')
