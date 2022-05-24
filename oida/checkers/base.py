import ast
from typing import ClassVar, NamedTuple


class Violation(NamedTuple):
    line: int
    column: int
    message: str


class Checker(ast.NodeVisitor):
    slug: ClassVar[str]

    def __init__(self, module: str | None, name: str) -> None:
        self.module = module
        self.name = name
        self.violations: list[Violation] = []

    def report_violation(self, node: ast.AST, message: str) -> None:
        self.violations.append(
            Violation(
                line=node.lineno,
                column=node.col_offset,
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
