import pytest

from oida.checkers import AppIsolationChecker
from oida.checkers.base import Violation

pytestmark = pytest.mark.module(name="selectors", module="project.component.app")


@pytest.mark.module(
    """\
    from project.other.app.services import service
    service()
    """
)
def test_app_isolation_private_service_import(
    checker: AppIsolationChecker, violation: Violation
) -> None:
    assert violation == Violation(
        line=2,
        column=0,
        message='Private attribute "project.other.app.services.service" referenced',
    )


@pytest.mark.module(
    """\
    from project.other.services import service
    service()
    """
)
def test_app_isolation_public_service_import(
    checker: AppIsolationChecker, violations: list[Violation]
) -> None:
    assert violations == []


@pytest.mark.module(
    """\
    from project.other.app.selectors import selector
    selector()
    """
)
def test_app_isolation_private_selector_import(
    checker: AppIsolationChecker, violation: Violation
) -> None:
    assert violation == Violation(
        line=2,
        column=0,
        message='Private attribute "project.other.app.selectors.selector" referenced',
    )


@pytest.mark.module("from project.other.selectors import selector")
def test_app_isolation_public_selector_import(
    checker: AppIsolationChecker, violations: list[Violation]
) -> None:
    assert violations == []


@pytest.mark.module(
    """\
    from project.other.app.models import Model

    def selector() -> None:
        Model.objects.get()
    """
)
def test_app_isolation_reference_violation(
    checker: AppIsolationChecker, violation: Violation
) -> None:
    assert violation == Violation(
        line=4,
        column=4,
        message='Private attribute "project.other.app.models.Model" referenced',
    )


@pytest.mark.module(
    """\
    from project.component.app.models import Model

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
def test_app_isolation_top_level_import(
    checker: AppIsolationChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
    def selector() -> None:
        from project.other.app.models import Model
        Model.objects.get()
    """
)
def test_app_isolation_reference_violation_non_top_level_import(
    checker: AppIsolationChecker, violation: Violation
) -> None:
    assert violation == Violation(
        line=3,
        column=4,
        message='Private attribute "project.other.app.models.Model" referenced',
    )


@pytest.mark.module(
    """\
    from project.other.app.models import Model

    def selector(model: Model) -> None: ...
    """
)
def test_app_isolation_parameter_annotation(
    checker: AppIsolationChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
    from project.other.app.models import Model
    variable: Model
    """
)
def test_app_isolation_variable_annotation(
    checker: AppIsolationChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
    from project.other.app.models import Model
    variable: Model = ...
    """
)
def test_app_isolation_assign_annotation(
    checker: AppIsolationChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.component_config(allowed_imports=["project.other.app.models.Model"])
@pytest.mark.module(
    """\
    from project.other.app.models import Model
    Model.objects.get()
    """
)
def test_app_isolation_allowed_import(
    checker: AppIsolationChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.component_config(allowed_imports=["project.other.app.models.*"])
@pytest.mark.module(
    """\
    from project.other.app.models import Model
    Model.objects.get()
    """
)
def test_app_isolation_allowed_import_star(
    checker: AppIsolationChecker, violations: list[Violation]
) -> None:
    assert not violations
