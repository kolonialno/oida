import ast

from ..module import Module
from ..reporter import Reporter


class Checker(ast.NodeVisitor):
    reporter: Reporter
    module: Module

    def check(self, module: Module, reporter: Reporter) -> None:
        self.reporter = reporter
        self.module = module

        self.visit(module.ast)

    def report_violation(self, node: ast.AST, message: str) -> None:
        self.reporter.report_violation(
            file=self.module.path,
            line=node.lineno,
            column=node.col_offset,
            message=message,
        )
