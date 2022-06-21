import pytest

from oida.checkers import Code, RelativeImportsChecker, Violation

pytestmark = pytest.mark.module(name="selectors", module="project.app")


@pytest.mark.module("from ..other_app import something")
def test_invalid_relative_import(
    checker: RelativeImportsChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=1,
            column=0,
            code=Code.ODA001,
            message='Relative import outside app: "..other_app"',
        )
    ]


@pytest.mark.module(
    """\
    def function():
        from ..other_app import something
    """
)
def test_invalid_relative_import_inline(
    checker: RelativeImportsChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=2,
            column=4,
            code=Code.ODA001,
            message='Relative import outside app: "..other_app"',
        )
    ]


@pytest.mark.module("from .models import Model")
def test_valid_relative_import(
    checker: RelativeImportsChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
        def my_method():
            from .models import Model
    """
)
def test_valid_relative_import_inline(
    checker: RelativeImportsChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module("from . import models")
def test_valid_relative_module_import(
    checker: RelativeImportsChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module("from .. import models")
def test_invalid_relative_module_import(
    checker: RelativeImportsChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=1,
            column=0,
            code=Code.ODA001,
            message='Relative import outside app: ".."',
        )
    ]
