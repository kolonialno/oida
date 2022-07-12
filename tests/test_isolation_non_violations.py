import pytest

from oida.checkers import ComponentIsolationChecker
from oida.checkers.base import Violation

pytestmark = pytest.mark.module(name="selectors", module="project.component.app")


@pytest.mark.module(
    """\
    from project.other.services import service
    service()
    """
)
def test_app_isolation_public_service_import(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that imports from public components are not caught"""
    assert not violations


@pytest.mark.module("from project.other.selectors import selector")
def test_app_isolation_public_selector_import(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that an unused import does not trigger any violations"""
    assert not violations


@pytest.mark.module(
    """\
    from project.component.app.models import Model

    def selector() -> None:
        Model.objects.get()
    """
)
def test_app_isolation_internal_app_reference_import_from(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that attribute access in function bodies are caught"""
    assert not violations


@pytest.mark.module(
    """\
    import project.component.services.private as private
    private.fn()
    """
)
def test_app_isolation_internal_app_reference_import(
    checker: ComponentIsolationChecker, violations: list[Violation]
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
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that function calls in function bodies are caught"""
    assert not violations


@pytest.mark.module(
    """\
    from project.other.app.models import Model

    def selector(model: Model) -> None: ...
    """
)
def test_app_isolation_parameter_annotation(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that imports can be used in parameter type annotations"""
    assert not violations


@pytest.mark.module(
    """\
    from project.other.app.models import Model
    variable: Model
    """
)
def test_app_isolation_variable_annotation(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that imports can be used in variable annotations without assignments"""
    assert not violations


@pytest.mark.module(
    """\
    from project.other.app.models import Model
    variable: Model = ...
    """
)
def test_app_isolation_assign_annotation(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """That that imports can be used in type annotations with assignments"""
    assert not violations


@pytest.mark.module(
    """\
    from project.other.app import services
    something_else.services
    """
)
def test_app_isolation_false_positive(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that an imported name is not mistaked with an attribute"""
    assert not violations


@pytest.mark.module(
    """\
    def function():
        from project.other.services import foo
        foo()
    """
)
def test_app_isolation_function_function_body(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that imports in a function body does not generate violations"""
    assert not violations


@pytest.mark.module(
    """\
    from project.other import services
    services.service()
    """
)
def test_isolation_component_service_import(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
    from project.other import services
    services.service().something
    """
)
def test_isolation_component_service_call_attribute(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
    import project
    project.other.services.service()
    """
)
def test_isolation_project_root_import(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
    import project.other.services
    project.other.services.service()
    """
)
def test_isolation_project_component_services_import(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
    from project.other.services import service
    service()
    """
)
def test_isloation_project_component_service(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
    from third_party.other.app.services import service
    service()
    """
)
def test_isloation_third_pary_deep_import_from(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
    from third_party import service
    service()
    """
)
def test_isloation_third_party_simple_import_from(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
    import third_party
    third_pary.foo.bar.baz.service()
    """
)
def test_isloation_third_party_simple_import(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.pyproject_toml(
    """\
    [tool.oida]
    ignored_modules = ['project.*.*.tests']
    """
)
@pytest.mark.module(
    """\
    from project.other.app.services import service
    service()
    """,
    module="project.component.app.tests",
    name="test_foobar",
)
def test_ignored_paths_wildcard(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    assert not violations
