import ast
import enum
from typing import ClassVar, NamedTuple

from ..config import Config


class Code(int, enum.Enum):
    ODA001 = 1  # Relative import outside app
    ODA002 = 2  # Invalid statement in config
    ODA003 = 3  # Invalid ALLOWED_IMPORTS statement in config
    ODA004 = 4  # Invalid ALLOWED_FOREIGN_KEYS statement in config
    ODA005 = 5  # Private attribute referenced


class Violation(NamedTuple):
    line: int
    column: int
    code: Code
    message: str


class Checker(ast.NodeVisitor):
    slug: ClassVar[str]

    def __init__(
        self, module: str | None, name: str, component_config: Config | None
    ) -> None:
        self.module = module
        self.name = name
        self.component_config = component_config
        self.violations: list[Violation] = []

    def report_violation(self, node: ast.AST, code: Code, message: str) -> None:
        self.violations.append(
            Violation(
                line=node.lineno,
                column=node.col_offset,
                code=code,
                message=message,
            )
        )

    def resolve_relative_import(self, name: str | None, level: int) -> str:
        """Resolve a relative module name to an absolute one."""

        # TODO: We can't crash on invalid code

        if not self.module:
            raise ImportError("attempted relative import beyond top-level package")

        bits = self.module.rsplit(".", level - 1)
        if len(bits) < level:
            raise ImportError("attempted relative import beyond top-level package")
        base = bits[0]
        return "{}.{}".format(base, name) if name else base
