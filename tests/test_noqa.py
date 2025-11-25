import pytest

from oida.checkers import Code, ComponentIsolationChecker, Violation
from oida.utils import parse_noida_comment

pytestmark = pytest.mark.module(name="selectors", module="project.component.app")


def test_parse_noida_comment_no_comment() -> None:
    """Test parsing line without noida comment"""
    assert parse_noida_comment("x = 1") is None
    assert parse_noida_comment("from foo import bar") is None


def test_parse_noida_comment_generic() -> None:
    """Test parsing generic noida comment"""
    assert parse_noida_comment("x = 1  # noida") == set()
    assert parse_noida_comment("x = 1  #noida") == set()
    assert parse_noida_comment("x = 1  # NOIDA") == set()


def test_parse_noida_comment_specific_code() -> None:
    """Test parsing noida comment with specific code"""
    assert parse_noida_comment("x = 1  # noida: ODA005") == {"ODA005"}
    assert parse_noida_comment("x = 1  # noida:ODA005") == {"ODA005"}
    assert parse_noida_comment("x = 1  # NOIDA: ODA005") == {"ODA005"}


def test_parse_noida_comment_multiple_codes() -> None:
    """Test parsing noida comment with multiple codes"""
    assert parse_noida_comment("x = 1  # noida: ODA005, ODA001") == {"ODA005", "ODA001"}
    assert parse_noida_comment("x = 1  # noida: ODA005,ODA001") == {"ODA005", "ODA001"}
    assert parse_noida_comment("x = 1  # noida: ODA005 , ODA001") == {
        "ODA005",
        "ODA001",
    }


@pytest.mark.module(
    """\
    from project.other.app.services import service
    service()  # noida
    """
)
def test_noida_generic_ignores_violation(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that generic noida comment ignores all violations on that line"""
    assert violations == []
    assert checker.referenced_imports == {"project.other.app.services.service"}


@pytest.mark.module(
    """\
    from project.other.app.services import service
    service()  # noida: ODA005
    """
)
def test_noida_specific_code_ignores_violation(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that specific noida comment ignores matching violation"""
    assert violations == []
    assert checker.referenced_imports == {"project.other.app.services.service"}


@pytest.mark.module(
    """\
    from project.other.app.services import service
    service()  # noida: ODA001
    """
)
def test_noida_different_code_does_not_ignore(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that noida comment with different code does not ignore violation"""
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
    service()  # noida: ODA005, ODA001
    """
)
def test_noida_multiple_codes_ignores_matching(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that noida comment with multiple codes ignores matching violation"""
    assert violations == []
    assert checker.referenced_imports == {"project.other.app.services.service"}


@pytest.mark.module(
    """\
    from project.other.app.models import Model

    def selector() -> None:
        Model.objects.get()  # noida: ODA005
    """
)
def test_noida_in_function_body(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that noida comment works in function bodies"""
    assert violations == []
    assert checker.referenced_imports == {"project.other.app.models.Model"}


@pytest.mark.module(
    """\
    from project.other.app.models import Model

    def selector() -> None:
        Model.objects.get()
        Model.objects.filter()  # noida
    """
)
def test_noida_only_affects_its_line(
    checker: ComponentIsolationChecker, violations: list[Violation]
) -> None:
    """Test that noida comment only affects violations on its own line"""
    assert violations == [
        Violation(
            line=4,
            column=4,
            code=Code.ODA005,
            message='Private attribute "project.other.app.models.Model" referenced',
        )
    ]
    assert checker.referenced_imports == {"project.other.app.models.Model"}
