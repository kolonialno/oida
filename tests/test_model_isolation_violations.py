import pytest

from oida.checkers import Code, ComponentModelIsolationChecker, Violation

pytestmark = pytest.mark.module(name="models", module="project.component.app")


@pytest.mark.module(
    """\
    from django.db import models

    class MyModel(models.Model):
        fk = models.ForeignKey("other.OtherModel")
    """
)
def test_foreignkey_to_other_app_1(
    checker: ComponentModelIsolationChecker, violations: list[Violation]
) -> None:
    """Test that private function calls at the module level is caught"""
    assert violations == [
        Violation(
            line=4,
            column=9,
            code=Code.ODA006,
            message="Related field to a different app: MyModel.fk",
        )
    ]


@pytest.mark.module(
    """\
    from django.db.models import ForeignKey

    class MyModel(models.Model):
        fk = ForeignKey("other.OtherModel")
    """
)
def test_foreignkey_to_other_app_2(
    checker: ComponentModelIsolationChecker, violations: list[Violation]
) -> None:
    """Test that private function calls at the module level is caught"""
    assert violations == [
        Violation(
            line=4,
            column=9,
            code=Code.ODA006,
            message="Related field to a different app: MyModel.fk",
        )
    ]


@pytest.mark.module(
    """\
    import django.db.models
    from project.other.models import OtherModel

    class MyModel(models.Model):
        fk = django.db.models.ForeignKey(OtherModel)
    """
)
def test_foreignkey_to_other_app_3(
    checker: ComponentModelIsolationChecker, violations: list[Violation]
) -> None:
    """Test that private function calls at the module level is caught"""
    assert violations == [
        Violation(
            line=5,
            column=9,
            code=Code.ODA006,
            message="Related field to a different app: MyModel.fk",
        )
    ]


@pytest.mark.module(
    """\
    from django.db import models
    from project.other import models as other_models

    class MyModel(models.Model):
        fk = models.OneToOneField(to=other_models.OtherModel)
    """
)
def test_foreignkey_to_other_app_4(
    checker: ComponentModelIsolationChecker, violations: list[Violation]
) -> None:
    """Test that private function calls at the module level is caught"""
    assert violations == [
        Violation(
            line=5,
            column=9,
            code=Code.ODA006,
            message="Related field to a different app: MyModel.fk",
        )
    ]


@pytest.mark.component_config(allowed_foreign_keys=["MyModel.fk"])
@pytest.mark.module(
    """\
    from django.db import models
    from project.other import models as other_models

    class MyModel(models.Model):
        fk = models.OneToOneField(to=other_models.OtherModel)
    """
)
def test_foreignkey_to_other_app_5(
    checker: ComponentModelIsolationChecker, violations: list[Violation]
) -> None:
    """Test that private function calls at the module level is caught"""
    assert not violations
