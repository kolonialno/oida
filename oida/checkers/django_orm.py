import ast

from .base import Checker, Code


class SelectForUpdateChecker(Checker):
    """
    Check that all Django ORM select_for_update() calls specify the 'of' argument.

    Example violations:
        Model.objects.select_for_update()  # <-- Not allowed
        queryset.select_for_update(nowait=True)  # <-- Not allowed

    Valid usage:
        Model.objects.select_for_update(of=("self",))
        queryset.select_for_update(of=("some_model", "other_model"))
    """

    slug = "django-select-for-update"

    def visit_Call(self, node: ast.Call) -> None:
        # Check if this is a call to a method named 'select_for_update'
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "select_for_update"
        ):
            # Check if the 'of' argument is present in the keyword arguments
            has_of_argument = any(keyword.arg == "of" for keyword in node.keywords)

            if not has_of_argument:
                self.report_violation(
                    node,
                    Code.ODA006,
                    "select_for_update() must specify the 'of' argument",
                )

        # Continue visiting child nodes
        self.generic_visit(node)
