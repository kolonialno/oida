import ast
from typing import Any

from ..config import SubserviceConfig
from ..module import Module
from ..reporter import Reporter


class Checker(ast.NodeVisitor):
    reporter: Reporter
    module: Module
    config: dict[str, SubserviceConfig]

    def check(
        self,
        module: Module,
        reporter: Reporter,
        config: dict[str, SubserviceConfig] | None,
    ) -> Any:
        self.reporter = reporter
        self.module = module
        self.config = config if config is not None else {}

        return self.visit(module.ast)

    def report_violation(self, node: ast.AST, message: str) -> None:
        self.reporter.report_violation(
            file=self.module.path,
            line=node.lineno,
            column=node.col_offset,
            message=message,
        )
