import textwrap
from pathlib import Path
from typing import Type, get_type_hints

import pytest
from oida.checkers.base import Checker
from oida.module import Module
from oida.reporter import Violation


class TestReporter:
    def __init__(self) -> None:
        self.violations: list[Violation] = []

    def report_violation(
        self, file: Path, line: int, column: int, message: str
    ) -> None:
        self.violations.append(Violation(file, line, column, message))


@pytest.fixture
def reporter() -> TestReporter:
    """Get a reporter that collects violations in an array"""

    return TestReporter()


@pytest.fixture
def violations(
    request: pytest.FixtureRequest, reporter: TestReporter
) -> list[Violation]:
    """Get all violations reported by the checker fixture"""

    # Make sure the checker fixture has run
    request.getfixturevalue("checker")
    return reporter.violations


@pytest.fixture
def violation(violations: list[Violation]) -> Violation:
    """Convenience fixture when you only expect one violation"""

    assert len(violations) == 1
    return violations[0]


@pytest.fixture
def checker(request: pytest.FixtureRequest, reporter: TestReporter) -> Checker:
    """
    Run a checker on a module

    The module is defined throught the module marker and which checker to run
    is determined by the type annotation of the test function. Eg:

        @pytest.mark.module(name=..., package=..., path=..., content=...)
        def test_something(checker: MyChecker) -> None:
            ...
    """

    marker = request.node.get_closest_marker("module")

    assert marker, 'Missing "module" marker, required to use the "checker" fixture'

    assert "package" in marker.kwargs, "Missing package parameter to module marker"
    assert "name" in marker.kwargs, "Missing name parameter to module marker"
    assert "path" in marker.kwargs, "Missing path parameter to module marker"
    assert "content" in marker.kwargs, "Missing content parameter to module marker"

    module = Module(
        package=marker.kwargs["package"],
        name=marker.kwargs["name"],
        path=Path(marker.kwargs["path"]),
        content=textwrap.dedent(marker.kwargs["content"]),
    )

    # Infer the checker to use from the type hint of the fixture parameter
    type_hints = get_type_hints(request.function)
    assert "checker" in type_hints, "Missing type annotation for checker parameter"
    checker_cls: Type[Checker] = type_hints["checker"]
    assert issubclass(
        checker_cls, Checker
    ), f'"{checker_cls.__name__}" is not a subclass of Checker'

    checker = checker_cls()
    checker.check(module, reporter)
    return checker
