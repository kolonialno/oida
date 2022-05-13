import ast

from .base import Checker


class CheckServiceAndSelectorImports(Checker):
    """
    Check that all services/selectors are imported from root
    """

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level > 0 or not self.module.package or not node.module:
            return

        root_package = self.module.package.split(".", 1)[0]
        components = node.module.split(".")

        # Ignore imports from third party libraries
        if components[0] != root_package:
            return

        if "services" in components and components[-1] != "services":
            self.report_violation(node, f"Invalid service import: {node.module}")
        if "selectors" in components and components[-1] != "selectors":
            self.report_violation(node, f"Invalid selector import: {node.module}")


class CheckRelativeImports(Checker):
    """
    Check that no relative imports are extending beyond an app
    """

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level == 0 or not self.module.package:
            return

        path = self.module.package.split(".", 2)
        if len(path) < 3:
            return

        root, app, *_ = path
        absolute_import = self.module.resolve_relative_import(node.module, node.level)

        if not absolute_import.startswith(f"{root}.{app}."):
            self.report_violation(
                node,
                f"Relative import outside app: \"{'.'*node.level}{node.module if node.module else ''}\"",
            )
