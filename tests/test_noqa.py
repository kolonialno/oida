import pytest

from oida.checkers import Code, ComponentIsolationChecker, Violation
from oida.utils import parse_noqa_comment

pytestmark = pytest.mark.module(name="selectors", module="project.component.app")


def test_parse_noqa_comment_no_comment() -> None:
    """Test parsing line without noqa comment"""
    assert parse_noqa_comment("x = 1") is None
    assert parse_noqa_comment("from foo import bar") is None


def test_parse_noqa_comment_generic() -> None:
    """Test parsing generic noqa comment"""
    assert parse_noqa_comment("x = 1  # noqa") == set()
    assert parse_noqa_comment("x = 1  #noqa") == set()
    assert parse_noqa_comment("x = 1  # NOQA") == set()


def test_parse_noqa_comment_specific_code() -> None:
    """Test parsing noqa comment with specific code"""
    assert parse_noqa_comment("x = 1  # noqa: ODA005") == {"ODA005"}
    assert parse_noqa_comment("x = 1  # noqa:ODA005") == {"ODA005"}
    assert parse_noqa_comment("x = 1  # NOQA: ODA005") == {"ODA005"}


def test_parse_noqa_comment_multiple_codes() -> None:
    """Test parsing noqa comment with multiple codes"""
    assert parse_noqa_comment("x = 1  # noqa: ODA005, ODA001") == {"ODA005", "ODA001"}
    assert parse_noqa_comment("x = 1  # noqa: ODA005,ODA001") == {"ODA005", "ODA001"}
    assert parse_noqa_comment("x = 1  # noqa: ODA005 , ODA001") == {
        "ODA005",
        "ODA001",
    }


@pytest.mark.module(
    """\
    from project.other.app.services import service
    service()  # noqa
    """
)
def test_noqa_generic_ignores_violation(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that generic noqa comment ignores all violations on that line"""
    assert violations == []
    assert checker.referenced_imports == {"project.other.app.services.service"}


@pytest.mark.module(
    """\
    from project.other.app.services import service
    service()  # noqa: ODA005
    """
)
def test_noqa_specific_code_ignores_violation(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that specific noqa comment ignores matching violation"""
    assert violations == []
    assert checker.referenced_imports == {"project.other.app.services.service"}


@pytest.mark.module(
    """\
    from project.other.app.services import service
    service()  # noqa: ODA001
    """
)
def test_noqa_different_code_does_not_ignore(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that noqa comment with different code does not ignore violation"""
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
    from project.other.app.services import service
    service()  # noqa: ODA005, ODA001
    """
)
def test_noqa_multiple_codes_ignores_matching(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that noqa comment with multiple codes ignores matching violation"""
    assert violations == []
    assert checker.referenced_imports == {"project.other.app.services.service"}


@pytest.mark.module(
    """\
    from project.other.app.models import Model

    def selector() -> None:
        Model.objects.get()  # noqa: ODA005
    """
)
def test_noqa_in_function_body(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that noqa comment works in function bodies"""
    assert violations == []
    assert checker.referenced_imports == {"project.other.app.models.Model"}


@pytest.mark.module(
    """\
    from project.other.app.models import Model

    def selector() -> None:
        Model.objects.get()
        Model.objects.filter()  # noqa
    """
)
def test_noqa_only_affects_its_line(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that noqa comment only affects violations on its own line"""
    assert violations == [
        Violation(
            line=4,
            column=4,
            code=Code.ODA005,
            message='Private attribute "project.other.app.models.Model" referenced',
        )
    ]
    assert checker.referenced_imports == {"project.other.app.models.Model"}
