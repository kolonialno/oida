import pytest

from oida.checkers import Code, ConfigChecker, Violation

pytestmark = pytest.mark.module(name="confcomponent", module="project.component")


@pytest.mark.module("ALLOWED_IMPORTS = {'foo', 'bar'}")
def test_config_allowed_imports_no_annotation(
    checker: ConfigChecker, violations: list[Violation]
) -> None:
    assert not violations
    assert checker.parsed_config.allowed_imports == frozenset(("foo", "bar"))


@pytest.mark.module("ALLOWED_IMPORTS = None")
def test_config_allowed_imports_wrong_type(
    checker: ConfigChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=1,
            column=18,
            code=Code.ODA003,
            message="ALLOWED_IMPORTS should be a set of string literals",
        )
    ]


@pytest.mark.module("ALLOWED_IMPORTS = ('foo', 'bar')")
def test_config_allowed_imports_tuple_not_set(
    checker: ConfigChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=1,
            column=18,
            code=Code.ODA003,
            message="ALLOWED_IMPORTS should be a set of string literals",
        )
    ]


@pytest.mark.module("ALLOWED_IMPORTS = {'str', None}")
def test_config_allowed_imports_wrong_type_in_tuple(
    checker: ConfigChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=1,
            column=18,
            code=Code.ODA003,
            message="ALLOWED_IMPORTS should be a set of string literals",
        )
    ]


@pytest.mark.module("ALLOWED_IMPORTS: tuple[str, ...]")
def test_config_allowed_imports_type_only(
    checker: ConfigChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module("FOO = bar")
def test_config_unknown_constant(
    checker: ConfigChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=1,
            column=0,
            code=Code.ODA002,
            message='Unknown constant "FOO" assigned in component config',
        )
    ]


@pytest.mark.module("FOO, BAR = baz")
def test_config_unpack_assign(
    checker: ConfigChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=1,
            column=0,
            code=Code.ODA002,
            message="Unsupported assignment in component config",
        )
    ]


@pytest.mark.module("FOO: str = bar")
def test_config_unknown_constant_with_annotation(
    checker: ConfigChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=1,
            column=0,
            code=Code.ODA002,
            message='Unknown constant "FOO" assigned in component config',
        )
    ]


@pytest.mark.module("ALLOWED_FOREIGN_KEYS = {'foo', 'bar'}")
def test_config_allowed_foreign_keys(
    checker: ConfigChecker, violations: list[Violation]
) -> None:
    assert not violations
    assert checker.parsed_config.allowed_foreign_keys == frozenset(("foo", "bar"))
