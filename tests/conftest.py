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
            allowed_imports=frozenset(marker.kwargs.get("allowed_imports", ())),
            allowed_foreign_keys=frozenset(
                marker.kwargs.get("allowed_foreign_keys", ())
            ),
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
def violations(checker: Checker) -> list[Violation]:
    """Convenience fixture for getting checker violations"""

    return checker.violations


@pytest.fixture
def project_path(request: pytest.FixtureRequest, tmp_path: Path) -> Path:
    """
    Create a temporary directory with some files in. Looks for the
    project_files marker and automatically creates any file defined by that.
    """

    files: dict[str, str] = {}
    for marker in reversed(list(request.node.iter_markers("project_files"))):
        files.update(marker.args[0])

    for name, content in files.items():
        file_path = tmp_path / name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w+") as f:
            f.write(textwrap.dedent(content))

    return tmp_path
