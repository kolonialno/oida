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
