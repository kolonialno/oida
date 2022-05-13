import ast

from .base import Checker


class RelativeImportsChecker(Checker):
    """
    Check that no relative imports are extending beyond an app

    Example:
        # project/app/module.py
        from ..other_app import models  # <-- Not allowed
    """

    name = "relative-imports"

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        # Ignore absolute imports (level == 0) or modules/files that are not in
        # a package (can't use relative imports anyway)
        if node.level == 0 or not self.module.package:
            return

        # Ignore modules/files that are not in an app (at least two levels deep)
        module_path = self.module.package.split(".", 2)
        if len(module_path) < 2:
            return

        project, app, *_ = module_path
        absolute_import = self.module.resolve_relative_import(
            node.module, node.level
        ).split(".")

        if absolute_import[:2] != [project, app]:
            import_name = "." * node.level + (node.module if node.module else "")
            self.report_violation(node, f'Relative import outside app: "{import_name}"')
