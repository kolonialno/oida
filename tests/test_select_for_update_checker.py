import pytest

from oida.checkers import Code, SelectForUpdateChecker, Violation

pytestmark = pytest.mark.module(name="selectors", module="project.app")


@pytest.mark.module("Model.objects.select_for_update()")
def test_select_for_update_without_of_argument(
    checker: SelectForUpdateChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=1,
            column=0,
            code=Code.ODA006,
            message="select_for_update() must specify the 'of' argument",
        )
    ]


@pytest.mark.module("queryset.select_for_update(nowait=True)")
def test_select_for_update_with_other_arguments_but_no_of(
    checker: SelectForUpdateChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=1,
            column=0,
            code=Code.ODA006,
            message="select_for_update() must specify the 'of' argument",
        )
    ]


@pytest.mark.module("Model.objects.filter(active=True).select_for_update()")
def test_select_for_update_chained_without_of(
    checker: SelectForUpdateChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=1,
            column=0,
            code=Code.ODA006,
            message="select_for_update() must specify the 'of' argument",
        )
    ]


@pytest.mark.module(
    """\
    def get_items():
        return Model.objects.select_for_update()
    """
)
def test_select_for_update_in_function_without_of(
    checker: SelectForUpdateChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=2,
            column=11,
            code=Code.ODA006,
            message="select_for_update() must specify the 'of' argument",
        )
    ]


@pytest.mark.module('Model.objects.select_for_update(of=("self",))')
def test_select_for_update_with_of_self(
    checker: SelectForUpdateChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module('queryset.select_for_update(of=("some_model", "other_model"))')
def test_select_for_update_with_of_multiple_models(
    checker: SelectForUpdateChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
    Model.objects.select_for_update(
        of=("some_model", "other_model")
    )
    """
)
def test_select_for_update_multiline_with_of(
    checker: SelectForUpdateChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module('Model.objects.select_for_update(nowait=True, of=("self",))')
def test_select_for_update_with_of_and_other_arguments(
    checker: SelectForUpdateChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
    def get_items():
        return Model.objects.select_for_update(of=("self",))
    """
)
def test_select_for_update_in_function_with_of(
    checker: SelectForUpdateChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
    # Valid usage
    Model.objects.select_for_update(of=("self",))

    # Invalid usage
    Model.objects.select_for_update()
    """
)
def test_mixed_valid_and_invalid_usage(
    checker: SelectForUpdateChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=5,
            column=0,
            code=Code.ODA006,
            message="select_for_update() must specify the 'of' argument",
        )
    ]


@pytest.mark.module(
    """\
    Model.objects.select_for_update()
    OtherModel.objects.select_for_update()
    """
)
def test_multiple_violations(
    checker: SelectForUpdateChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=1,
            column=0,
            code=Code.ODA006,
            message="select_for_update() must specify the 'of' argument",
        ),
        Violation(
            line=2,
            column=0,
            code=Code.ODA006,
            message="select_for_update() must specify the 'of' argument",
        ),
    ]


@pytest.mark.module(
    """\
    Model.objects.filter(active=True).select_for_update(of=("self",))
    """
)
def test_select_for_update_chained_with_of(
    checker: SelectForUpdateChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
    # This should not trigger a violation - it's not a method call
    select_for_update = "some string"
    """
)
def test_select_for_update_as_variable_name(
    checker: SelectForUpdateChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
    def select_for_update():
        pass

    select_for_update()
    """
)
def test_select_for_update_as_function_name(
    checker: SelectForUpdateChecker, violations: list[Violation]
) -> None:
    # This should NOT trigger a violation - the checker only checks method calls
    # (obj.select_for_update()), not standalone function calls (select_for_update())
    # This is the desired behavior since we only care about Django ORM method calls
    assert not violations
