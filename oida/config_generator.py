import ast
from pathlib import Path
from typing import cast

import libcst as cst
from libcst import matchers as m
from libcst.helpers.common import ensure_type

from .checkers import ComponentIsolationChecker
from .config import get_rule_for_violation
from .discovery import get_module, get_project_config


def collect_violations(project_root: Path) -> dict[Path, set[str]]:
    """
    Collect violations in components. Returns a dictionary mapping from
    component path to a set of violations.
    """

    violations: dict[Path, set[str]] = {}

    for path in project_root.iterdir():
        if path.is_dir() and (path / "__init__.py").exists():
            violations[path] = collect_violations_in_dir(path)

    return violations


def collect_violations_in_dir(path: Path) -> set[str]:
    """
    Recursively collect all violations in a directory.
    """

    violations: set[str] = set()
    for child in path.iterdir():
        if child.is_dir():
            if (child / "__init__.py").exists():
                violations |= collect_violations_in_dir(child)
        elif child.suffix == ".py":
            violations |= collect_violations_in_file(child)

    return violations


def collect_violations_in_file(path: Path) -> set[str]:
    """
    Collect all violations in the given Python file.
    """

    module = get_module(path)
    project_config = get_project_config(path.parent)
    checker = ComponentIsolationChecker(module, path.stem, None, project_config)
    with open(path) as f:
        checker.visit(ast.parse(f.read(), str(path)))
    return checker.referenced_imports


def update_component_config(node: cst.Module, allowed_imports: set[str]) -> cst.Module:
    """
    Update a compontent config. Returns a modified copy of the provided cst.
    """

    new_body: list[cst.SimpleStatementLine | cst.BaseCompoundStatement] = []

    allowed_imports_matcher = m.SimpleStatementLine(
        [
            m.OneOf(
                m.AnnAssign(target=m.Name("ALLOWED_IMPORTS")),
                m.Assign(targets=[m.AssignTarget(m.Name("ALLOWED_IMPORTS"))]),
            )
        ]
    )

    updated_existing = False
    for statement in node.body:
        if m.matches(statement, allowed_imports_matcher):
            new_value = update_allowed_imports_statement(
                cast(
                    cst.AnnAssign | cst.Assign,
                    ensure_type(statement, cst.SimpleStatementLine).body[0],
                ),
                allowed_imports,
            )
            if new_value is cst.RemovalSentinel:
                continue
            else:
                new_body.append(statement.with_changes(body=[new_value]))
            updated_existing = True
        else:
            new_body.append(statement)

    # If we did not update an existing allowed imports line we need to create
    # one now
    if not updated_existing and allowed_imports:
        new_body.append(
            cst.SimpleStatementLine(
                [
                    cst.AnnAssign(
                        target=cst.Name("ALLOWED_IMPORTS"),
                        annotation=cst.Annotation(
                            cst.parse_expression(
                                "set[str]", config=node.config_for_parsing
                            )
                        ),
                        value=cst.Set(
                            [
                                cst.Element(cst.SimpleString(f'"{value}"'))
                                for value in sorted(allowed_imports)
                            ]
                        ),
                    )
                ]
            )
        )

    return node.with_changes(body=new_body)


def update_allowed_imports_statement(
    node: cst.AnnAssign | cst.Assign, violations: set[str]
) -> cst.AnnAssign | cst.Assign | type[cst.RemovalSentinel]:
    """
    Update an assignment expression where the ALLOWED_IMPORTS variable is assigned to.
    """

    if not violations:
        return cst.RemovalSentinel

    if node.value and m.matches(node.value, m.Set()):
        value = ensure_type(node.value, cst.Set)
        current_rules: set[str] = {
            ensure_type(element.value, cst.SimpleString).evaluated_value
            for element in value.elements
        }

        updated_rules = update_allowed_imports(current_rules, violations)

        new_elements = [
            element
            for element in value.elements
            if ensure_type(element.value, cst.SimpleString).evaluated_value
            in updated_rules
        ]

        for rule in sorted(updated_rules):
            if rule in current_rules:
                continue

            new_elements.append(cst.Element(cst.SimpleString(f'"{rule}"')))

        value = value.with_changes(elements=new_elements)
    else:
        value = cst.Set(
            [cst.Element(cst.SimpleString(f'"{rule}"')) for rule in sorted(violations)]
        )

    return node.with_changes(value=value)


def update_allowed_imports(
    current_rules: set[str], recoded_violations: set[str]
) -> set[str]:
    """
    Update a list of violations. This will remove unused warnings and add new
    ones if needed.
    """

    new_rules: set[str] = set()

    for violation in recoded_violations:
        # Already covered by another rule
        if get_rule_for_violation(new_rules, violation):
            continue

        if rule := get_rule_for_violation(current_rules, violation):
            new_rules.add(rule)
        else:
            new_rules.add(violation)

    return new_rules
