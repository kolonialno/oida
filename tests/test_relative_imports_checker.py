from unittest import mock

import pytest

from oida.checkers import RelativeImportsChecker
from oida.reporter import Violation


@pytest.mark.module(
    name="selectors",
    package="project.app",
    path="project/app/selectors.py",
    content="from ..other_app import something",
)
def test_invalid_relative_import(
    checker: RelativeImportsChecker, violation: Violation
) -> None:
    assert violation == Violation(
        file=mock.ANY,
        line=1,
        column=0,
        message='Relative import outside app: "..other_app"',
    )


@pytest.mark.module(
    name="selectors",
    package="project.app",
    path="project/app/selectors.py",
    content="from .models import Model",
)
def test_valid_relative_import(
    checker: RelativeImportsChecker, violations: list[Violation]
) -> None:
    assert violations == []
