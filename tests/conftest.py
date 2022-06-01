import textwrap
from pathlib import Path
from typing import Type, get_type_hints

import pytest

from oida.checkers.base import Checker, Violation
from oida.config import Config
from oida.module import Module


@pytest.fixture
def checker(request: pytest.FixtureRequest) -> Checker:
    """
    Run a checker on a module

    The module is defined throught the module marker and which checker to run
    is determined by the type annotation of the test function. Eg:

        @pytest.mark.module("...", name=..., module=...)
        def test_something(checker: MyChecker) -> None:
            ...
    """

    config: Config | None = None
    module: str | None = None
    name: str | None = None
    content: str | None = None

    marker = None
    for marker in reversed(list(request.node.iter_markers("module"))):
        if marker.args:
            content = marker.args[0]
        module = marker.kwargs.get("module", module)
        name = marker.kwargs.get("name", name)

    assert marker, 'Missing "module" marker, required to use the "checker" fixture'
    assert content is not None, "Missing module content"
    assert name, "Missing name parameter to module marker"

    if module:
        path = Path("/".join(module.split("."))) / f"{name}.py"
    else:
        path = Path(f"{name}.py")

    m = Module(module=module, name=name, path=path, content=textwrap.dedent(content))

    if marker := request.node.get_closest_marker("component_config"):
        config = Config(
            allowed_imports=tuple(marker.kwargs.get("allowed_imports", ())),
            allowed_foreign_keys=tuple(marker.kwargs.get("allowed_foreign_keys", ())),
        )

    # Infer the checker to use from the type hint of the fixture parameter
    type_hints = get_type_hints(request.function)
    assert "checker" in type_hints, "Missing type annotation for checker parameter"
    checker_cls: Type[Checker] = type_hints["checker"]
    assert issubclass(
        checker_cls, Checker
    ), f'"{checker_cls.__name__}" is not a subclass of Checker'

    checker = checker_cls(module=m.module, name=m.name, component_config=config)
    checker.visit(m.ast)
    return checker


@pytest.fixture
def violation(checker: Checker) -> Violation:
    """Convenience fixture when you only expect one violation"""

    assert len(checker.violations) == 1
    return checker.violations[0]


@pytest.fixture
def violations(checker: Checker) -> list[Violation]:
    """Convenience fixture for getting checker violations"""

    return checker.violations
