import ast
from functools import cached_property
from pathlib import Path


class Module:
    def __init__(
        self, module: str | None, name: str, path: Path, content: str | None = None
    ) -> None:
        self.module = module
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

        if not self.module:
            raise ImportError("attempted relative import beyond top-level module")

        bits = self.module.rsplit(".", level - 1)
        if len(bits) < level:
            raise ImportError("attempted relative import beyond top-level module")
        base = bits[0]
        return "{}.{}".format(base, name) if name else base
