import pytest

from oida.checkers import Code, ComponentIsolationChecker, Violation

pytestmark = pytest.mark.module(name="selectors", module="project.component.app")


@pytest.mark.module(
    """\
    from project.other.app.services import service
    service()
    """
)
def test_app_isolation_private_service_import(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that private function calls at the module level is caught"""
    assert violations == [
        Violation(
            line=2,
            column=0,
            code=Code.ODA005,
            message='Private attribute "project.other.app.services.service" referenced',
        )
    ]
    assert checker.referenced_imports == {"project.other.app.services.service"}


@pytest.mark.module(
    """\
    from project.other.app.models import Model

    def selector() -> None:
        Model.objects.get()
    """
)
def test_app_isolation_reference_violation(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that attribute access in function bodies are caught"""
    assert violations == [
        Violation(
            line=4,
            column=4,
            code=Code.ODA005,
            message='Private attribute "project.other.app.models.Model" referenced',
        )
    ]
    assert checker.referenced_imports == {"project.other.app.models.Model"}


@pytest.mark.module(
    """\
    def selector() -> None:
        from project.other.app.models import Model
        Model.objects.get()
    """
)
def test_app_isolation_reference_violation_non_top_level_import(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that non-top level imports are also caught"""
    assert violations == [
        Violation(
            line=3,
            column=4,
            code=Code.ODA005,
            message='Private attribute "project.other.app.models.Model" referenced',
        )
    ]
    assert checker.referenced_imports == {"project.other.app.models.Model"}


@pytest.mark.module(
    """\
    from project.other.app import services
    services.private()
    """
)
def test_app_isolation_complex_import(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that access through another import is caught"""
    assert violations == [
        Violation(
            line=2,
            column=0,
            code=Code.ODA005,
            message='Private attribute "project.other.app.services.private" referenced',
        )
    ]
    assert checker.referenced_imports == {"project.other.app.services.private"}


@pytest.mark.module(
    """\
    from project.other import app
    app.models.Model()
    """
)
def test_isolation_attribute_access_violation(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=2,
            column=0,
            code=Code.ODA005,
            message='Private attribute "project.other.app.models.Model" referenced',
        )
    ]
    assert checker.referenced_imports == {"project.other.app.models.Model"}


@pytest.mark.module(
    """\
    import project
    project.other.app.services.service()
    """
)
def test_isolation_attribute_access_violation_root_import(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=2,
            column=0,
            code=Code.ODA005,
            message='Private attribute "project.other.app.services.service" referenced',
        )
    ]
    assert checker.referenced_imports == {"project.other.app.services.service"}


@pytest.mark.module(
    """\
    import project.other.app
    project.other.app.services.service()
    """
)
def test_isolation_attribute_access_violation_plain_import(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=2,
            column=0,
            code=Code.ODA005,
            message='Private attribute "project.other.app.services.service" referenced',
        )
    ]
    assert checker.referenced_imports == {"project.other.app.services.service"}


@pytest.mark.module(
    """\
    from project.other.app import models
    models.Model()
    """
)
def test_isolation_attribute_access_model_import(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=2,
            column=0,
            code=Code.ODA005,
            message='Private attribute "project.other.app.models.Model" referenced',
        )
    ]
    assert checker.referenced_imports == {"project.other.app.models.Model"}


@pytest.mark.module(
    """\
    from project.other.app import models
    models.Model.objects.all()
    """
)
def test_isolation_attribute_access_model_import_through_class(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=2,
            column=0,
            code=Code.ODA005,
            message='Private attribute "project.other.app.models.Model" referenced',
        )
    ]
    assert checker.referenced_imports == {"project.other.app.models.Model"}


@pytest.mark.skip("Not implemented yet")
@pytest.mark.module("import project.other.app.selectors.selector")
def test_isolation_unused_import_violation(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that an unused import triggers a violations"""
    assert violations == [
        Violation(
            line=0,
            column=0,
            code=Code.ODA005,
            message='Private attribute "project.other.app.selectors.selector" referenced',
        )
    ]
    assert checker.referenced_imports == {"project.other.app.selectors.select"}


@pytest.mark.pyproject_toml(
    """\
    [tool.oida]
    ignored_modules = ['project.*.tests']
    """
)
@pytest.mark.module(
    """\
    from project.other.app.services import service
    service()
    """,
    module="project",
    name="test_foobar",
)
def test_ignored_paths_shorter_path_than_ignore(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that ignores at a deeper path are not used"""
    assert violations == [
        Violation(
            line=2,
            column=0,
            code=Code.ODA005,
            message='Private attribute "project.other.app.services.service" referenced',
        )
    ]
    assert checker.referenced_imports == {"project.other.app.services.service"}
