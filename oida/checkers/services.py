import ast

from oida.checkers.base import Checker, Code
from oida.config import ComponentConfig, ProjectConfig


class KeywordOnlyChecker(Checker):
    """
    Check that service and selector functions use keyword-only parameters.

    Service and selector functions are defined by either being in files named
    services.py or selectors.py, or in directories named services/ or selectors/.

    All functions in these files should have the '*' separator to enforce
    keyword-only parameters (except for 'self' or 'cls' in methods).

    Example violations:
        def create_user(username, email):  # <-- Not allowed
            pass

        class UserService:
            def create(self, username, email):  # <-- Not allowed
                pass

    Valid usage:
        def create_user(*, username, email):
            pass

        class UserService:
            def create(self, *, username, email):
                pass

            def __init__(self, dependency):  # <-- __init__ and other dunder methods are allowed
                pass
    """

    slug = "service-selector-keyword-only"

    def __init__(
        self,
        module: str | None,
        name: str,
        component_config: ComponentConfig | None,
        project_config: ProjectConfig,
        source_lines: list[str] | None = None,
    ) -> None:
        super().__init__(module, name, component_config, project_config, source_lines)
        self._is_service_or_selector = self._check_if_service_or_selector()
        self._function_depth = 0  # Track nesting depth of functions
        self._class_depth = 0  # Track nesting depth of classes

    def _check_if_service_or_selector(self) -> bool:
        """
        Check if the current file is a service or selector file.

        Returns True if:
        - The file is named services.py or selectors.py
        - The file is in a services/ or selectors/ directory
        """
        # Check if file is named services.py or selectors.py
        if self.name in ("services", "selectors"):
            return True

        # Check if file is in services/ or selectors/ directory
        if self.module:
            # Check if module contains .services. or .selectors., or ends with .services or .selectors
            if ".services." in self.module or ".selectors." in self.module:
                return True
            if self.module.endswith(".services") or self.module.endswith(".selectors"):
                return True

        return False

    def _is_dunder_method(self, name: str) -> bool:
        """Check if the function name is a dunder method (e.g., __init__, __str__)."""
        return name.startswith("__") and name.endswith("__")

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Track class nesting depth."""
        self._class_depth += 1
        self.generic_visit(node)
        self._class_depth -= 1

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check regular function definitions."""
        self._check_function(node)
        self._function_depth += 1
        self.generic_visit(node)
        self._function_depth -= 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Check async function definitions."""
        self._check_function(node)
        self._function_depth += 1
        self.generic_visit(node)
        self._function_depth -= 1

    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """
        Check if a function uses keyword-only parameters.

        Functions should use the '*' separator to make all parameters keyword-only,
        except for 'self' or 'cls' in methods.

        Only checks top-level functions and methods of top-level classes.
        Inner functions and methods of nested classes are not checked.
        """
        # Only check if this is a service or selector file
        if not self._is_service_or_selector:
            return

        # Skip inner functions (functions defined inside other functions)
        if self._function_depth > 0:
            return

        # Skip methods of nested classes (classes defined inside other classes)
        if self._class_depth > 1:
            return

        # Skip dunder methods (e.g., __init__, __str__, __repr__)
        if self._is_dunder_method(node.name):
            return

        args = node.args

        # Determine if this is an instance/class method by checking the first parameter
        is_method = False
        if args.args:
            first_param_name = args.args[0].arg
            if first_param_name in ("self", "cls"):
                is_method = True

        # Count positional-or-keyword parameters
        positional_count = len(args.args)

        # For methods, the first parameter (self/cls) is allowed to be positional
        allowed_positional = 1 if is_method else 0

        # Check if there are more positional parameters than allowed
        if positional_count > allowed_positional:
            self.report_violation(
                node,
                Code.ODA007,
                "Service and selector functions must use keyword-only parameters (add * before parameters)",
            )
