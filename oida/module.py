import ast
from functools import cached_property
from pathlib import Path


class Module:
    def __init__(
        self, package: str | None, name: str, path: Path, content: str | None = None
    ) -> None:
        self.package = package
        self.name = name
        self.path = path
        self.content = content

    @cached_property
    def ast(self) -> ast.AST:
        if self.content is not None:
            return ast.parse(self.content, filename=str(self.path))
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
