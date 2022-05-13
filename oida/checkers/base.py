import ast

from ..state import Module


class Checker(ast.NodeVisitor):
    def check(self, module: Module) -> None:
        self.module = module

        self.visit(module.ast)

    def report_violation(self, node: ast.AST, message: str) -> None:
        print(f"{self.module.path}:{node.lineno}:{node.col_offset}: {message}")
