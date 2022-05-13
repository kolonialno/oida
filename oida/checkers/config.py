import ast
from typing import cast

from ..config import SubserviceConfig
from .base import Checker


class SubserviceConfigChecker(Checker):
    """
    Checker that validates a sub-service config dict.
    """

    def visit_Module(self, node: ast.Module) -> dict[str, SubserviceConfig] | None:

        if self.module.name != "confservice":
            return None

        config = None
        for statement in node.body:
            config = self.check_statement(statement)

        return config

    def check_statement(
        self, statement: ast.stmt
    ) -> dict[str, SubserviceConfig] | None:
        match statement:
            case ast.Assign(targets=[ast.Name("SUBSERVICES")], value=ast.Dict()):
                return self.parse(cast(ast.Dict, statement.value))
            case ast.Assign(targets=[ast.Name("SUBSERVICES")]):
                self.report_violation(
                    statement.value,
                    "Invalid sub-service config, should be a dict literal",
                )
            case ast.AnnAssign(target=ast.Name("SUBSERVICES"), value=ast.Dict()):
                return self.parse(cast(ast.Dict, statement.value))
            case ast.AnnAssign(target=ast.Name("SUBSERVICES"), value=value):
                if value is not None:
                    self.report_violation(
                        value, "Invalid sub-service config, should be a dict literal"
                    )

        return None

    def parse(self, node: ast.Dict) -> dict[str, SubserviceConfig]:
        """
        Parse a dict literal ast node that defines a subservice config.
        """

        subservices: dict[str, SubserviceConfig] = {}

        for key, value in zip(node.keys, node.values):

            match key, value:
                case ast.Constant(value=str(name)), ast.Dict():
                    subservices[name] = self._parse_subservice(cast(ast.Dict, value))
                case ast.Constant(value=str(name)), _:
                    self.report_violation(value, "Invalid sub-service config")
                case _:
                    self.report_violation(
                        cast(ast.AST, key), "Invalid sub-service config"
                    )

        return subservices

    def _parse_subservice(self, node: ast.Dict) -> SubserviceConfig:
        """
        Parse a single subservice config.
        """

        config: SubserviceConfig = {}

        for key, value in zip(node.keys, node.values):
            match key, value:
                case ast.Constant(value="database"), ast.Constant(value=str(name)):
                    config["database"] = name
                case ast.Constant(value="apps"), ast.List(elts=apps):
                    config["apps"] = self._parse_apps_list(apps)
                case ast.Constant(value=str(name)), _:
                    assert isinstance(key, ast.AST)
                    if name == "database":
                        self.report_violation(
                            key,
                            f'Invalid value for "{name}", should be a string literal',
                        )
                    elif name == "apps":
                        self.report_violation(
                            key,
                            f'Invalid value for "{name}", should be a list of string literals',
                        )
                    else:
                        self.report_violation(
                            key,
                            f'Unknown config key "{name}", choices are "database" or "apps"',
                        )
                case ast.AST(), _:
                    self.report_violation(
                        cast(ast.AST, key),
                        'Invalid config key, choices are "database" or "apps"',
                    )

        return config

    def _parse_apps_list(self, exprs: list[ast.expr]) -> list[str]:
        """
        Parse a list of apps.
        """

        items: list[str] = []

        for expr in exprs:
            match expr:
                case ast.Constant(value=str(value)):
                    items.append(value)
                case _:
                    self.report_violation(
                        expr,
                        'Invalid value for "apps", should be a list of string literals',
                    )

        return items
