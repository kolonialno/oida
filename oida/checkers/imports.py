import ast

from .base import Checker, Code


class RelativeImportsChecker(Checker):
    """
    Check that no relative imports are extending beyond an app

    Example:
        # project/app/module.py
        from ..other_app import models  # <-- Not allowed
    """

    slug = "relative-imports"

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        # Ignore absolute imports (level == 0) or modules/files that are not in
        # a package (can't use relative imports anyway)
        if node.level == 0 or not self.module:
            return

        # Ignore modules/files that are not in an app (at least two levels deep)
        module_path = self.module.split(".", 2)
        if len(module_path) < 2:
            return

        project, app, *_ = module_path
        absolute_import = self.resolve_relative_import(node.module, node.level).split(
            "."
        )

        if absolute_import[:2] != [project, app]:
            import_name = "." * node.level + (node.module if node.module else "")
            self.report_violation(
                node, Code.ODA001, f'Relative import outside app: "{import_name}"'
            )
