import ast
from functools import cached_property
from pathlib import Path


class Module:
    def __init__(self, package: str | None, name: str, path: Path) -> None:
        self.package = package
        self.name = name
        self.path = path

    @cached_property
    def ast(self) -> ast.AST:
        return ast.parse(self.path.read_bytes(), filename=str(self.path))

    def resolve_relative_import(self, name: str | None, level: int) -> str:
        """Resolve a relative module name to an absolute one."""

        if not self.package:
            raise ImportError("attempted relative import beyond top-level package")

        bits = self.package.rsplit(".", level - 1)
        if len(bits) < level:
            raise ImportError("attempted relative import beyond top-level package")
        base = bits[0]
        return "{}.{}".format(base, name) if name else base
