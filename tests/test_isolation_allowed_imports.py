import pytest

from oida.checkers import ComponentIsolationChecker
from oida.checkers.base import Violation

pytestmark = pytest.mark.module(name="selectors", module="project.component.app")


@pytest.mark.component_config(allowed_imports=["project.other.app.models.Model"])
@pytest.mark.module(
    """\
    from project.other.app.models import Model
    Model.objects.get()
    """
)
def test_app_isolation_allowed_import(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that allow imports will skip global attribute access"""
    assert not violations
    assert checker.referenced_imports == {"project.other.app.models.Model"}


@pytest.mark.component_config(allowed_imports=["project.other.app.models.*"])
@pytest.mark.module(
    """\
    from project.other.app.models import Model
    Model.objects.get()
    """
)
def test_app_isolation_allowed_import_star(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that wild card allow imports will skip global attribute access"""
    assert not violations
    assert checker.referenced_imports == {"project.other.app.models.Model"}
