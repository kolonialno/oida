from unittest import mock

import pytest

from oida.checkers import AppIsolationChecker
from oida.reporter import Violation

pytestmark = pytest.mark.module(name="selectors", package="project.app")


@pytest.mark.module("from project.other.services.private import service")
def test_app_isolation_private_service_import(
    checker: AppIsolationChecker, violation: Violation
) -> None:
    assert violation == Violation(
        file=mock.ANY,
        line=1,
        column=0,
        message='Non-public service imported from "project.other.services.private"',
    )


@pytest.mark.module("from project.other.services import service")
def test_app_isolation_public_service_import(
    checker: AppIsolationChecker, violations: list[Violation]
) -> None:
    assert violations == []


@pytest.mark.module("from project.other.selectors.private import selector")
def test_app_isolation_private_selector_import(
    checker: AppIsolationChecker, violation: Violation
) -> None:
    assert violation == Violation(
        file=mock.ANY,
        line=1,
        column=0,
        message='Non-public selector imported from "project.other.selectors.private"',
    )


@pytest.mark.module("from project.other.selectors import selector")
def test_app_isolation_public_selector_import(
    checker: AppIsolationChecker, violations: list[Violation]
) -> None:
    assert violations == []


@pytest.mark.module(
    """\
    from project.other.models import Model

    def selector() -> None:
        Model.objects.get()
    """
)
def test_app_isolation_reference_violation(
    checker: AppIsolationChecker, violation: Violation
) -> None:
    assert violation == Violation(
        file=mock.ANY,
        line=4,
        column=4,
        message='Private variable "project.other.models.Model" referenced',
    )


@pytest.mark.module(
    """\
    from project.app.models import Model

    def selector() -> None:
        Model.objects.get()
    """
)
def test_app_isolation_internal_app_reference(
    checker: AppIsolationChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
    from project.other.services import other_service

    def service() -> None:
        other_service()
    """
)
def test_app_isolation_service_import(
    checker: AppIsolationChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
    from project.other.selectors import other_selector

    def selector() -> None:
        other_selector()
    """
)
def test_app_isolation_selector_import(
    checker: AppIsolationChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
    def selector() -> None:
        from project.other.models import Model
        Model.objects.get()
    """
)
def test_app_isolation_reference_violation_non_top_level_import(
    checker: AppIsolationChecker, violation: Violation
) -> None:
    assert violation == Violation(
        file=mock.ANY,
        line=3,
        column=4,
        message='Private variable "project.other.models.Model" referenced',
    )


@pytest.mark.module(
    """\
    from project.other.models import Model

    def selector(model: Model) -> None: ...
    """
)
def test_app_isolation_parameter_annotation(
    checker: AppIsolationChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
    from project.other.models import Model
    variable: Model
    """
)
def test_app_isolation_variable_annotation(
    checker: AppIsolationChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
    from project.other.models import Model
    variable: Model = ...
    """
)
def test_app_isolation_assign_annotation(
    checker: AppIsolationChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.confservice(my_service={"apps": ["project.app", "project.other"]})
@pytest.mark.module(
    """\
    from project.other.models import Model

    Model.objects.al()
    """
)
def test_access_other_app_same_subservice(
    checker: AppIsolationChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.confservice(my_service={"apps": ["project.app", "project.other"]})
@pytest.mark.module("from project.other.services.private import service")
def test_access_private_service_same_subservice(
    checker: AppIsolationChecker, violations: list[Violation]
) -> None:
    assert not violations
