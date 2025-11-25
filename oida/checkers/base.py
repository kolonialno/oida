import ast
import enum
from typing import ClassVar, NamedTuple

from ..config import ComponentConfig, ProjectConfig
from ..utils import parse_noqa_comment


class Code(int, enum.Enum):
    ODA001 = 1  # Relative import outside app
    ODA002 = 2  # Invalid statement in config
    ODA003 = 3  # Invalid ALLOWED_IMPORTS statement in config
    ODA004 = 4  # Invalid ALLOWED_FOREIGN_KEYS statement in config
    ODA005 = 5  # Private attribute referenced
    ODA006 = 6  # select_for_update called without 'of' argument
    ODA007 = 7  # Service/selector function without keyword-only parameters


class Violation(NamedTuple):
    line: int
    column: int
    code: Code
    message: str


class Checker(ast.NodeVisitor):
    slug: ClassVar[str]

    def __init__(
        self,
        module: str | None,
        name: str,
        component_config: ComponentConfig | None,
        project_config: ProjectConfig,
        source_lines: list[str] | None = None,
    ) -> None:
        self.module = module
        self.name = name
        self.component_config = component_config
        self.project_config = project_config
        self.source_lines = source_lines
        self.violations: list[Violation] = []

    def _should_ignore_violation(self, line: int, code: Code) -> bool:
        """Check if a violation should be ignored due to a noqa comment."""
        if self.source_lines is None or line < 1 or line > len(self.source_lines):
            return False

        source_line = self.source_lines[line - 1]  # Convert 1-indexed to 0-indexed
        noqa_codes = parse_noqa_comment(source_line)

        if noqa_codes is None:
            # No noqa comment
            return False

        if not noqa_codes:
            # "# noqa" without specific codes - ignore all violations
            return True

        # Check if this specific code should be ignored
        code_str = f"ODA{code.value:03d}"
        return code_str in noqa_codes

    def report_violation(self, node: ast.AST, code: Code, message: str) -> None:
        if self._should_ignore_violation(node.lineno, code):
            return

        self.violations.append(
            Violation(
                line=node.lineno,
                column=node.col_offset,
                code=code,
                message=message,
            )
        )

    def resolve_relative_import(self, name: str | None, level: int) -> str | None:
        """Resolve a relative module name to an absolute one."""

        if not self.module:
            return None

        bits = self.module.rsplit(".", level - 1)
        if len(bits) < level:
            return None
        base = bits[0]
        return "{}.{}".format(base, name) if name else base
