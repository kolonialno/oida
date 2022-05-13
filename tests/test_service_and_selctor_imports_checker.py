from unittest import mock

import pytest

from oida.checkers import ServiceAndSelectorImportsChecker
from oida.reporter import Violation

pytestmark = pytest.mark.module(name="selectors", package="project.app")


@pytest.mark.module("from project.other.services.private import service")
def test_private_service_import(
    checker: ServiceAndSelectorImportsChecker, violation: Violation
) -> None:
    assert violation == Violation(
        file=mock.ANY,
        line=1,
        column=0,
        message='Non-public service imported from "project.other.services.private"',
    )


@pytest.mark.module("from project.other.services import service")
def test_public_service_import(
    checker: ServiceAndSelectorImportsChecker, violations: list[Violation]
) -> None:
    assert violations == []


@pytest.mark.module("from project.other.selectors.private import selector")
def test_private_selector_import(
    checker: ServiceAndSelectorImportsChecker, violation: Violation
) -> None:
    assert violation == Violation(
        file=mock.ANY,
        line=1,
        column=0,
        message='Non-public selector imported from "project.other.selectors.private"',
    )


@pytest.mark.module("from project.other.selectors import selector")
def test_public_selector_import(
    checker: ServiceAndSelectorImportsChecker, violations: list[Violation]
) -> None:
    assert violations == []
