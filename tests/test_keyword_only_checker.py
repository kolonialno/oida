import pytest

from oida.checkers import Code, KeywordOnlyChecker, Violation

# Default to testing in a services.py file
pytestmark = pytest.mark.module(name="services", module="project.app")


# Tests for violations


@pytest.mark.module(
    """\
def create_user(username, email):
    pass
"""
)
def test_function_without_keyword_only_params(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=1,
            column=0,
            code=Code.ODA007,
            message="Service and selector functions must use keyword-only parameters (add * before parameters)",
        )
    ]


@pytest.mark.module(
    """\
def get_user(user_id):
    pass
"""
)
def test_function_with_single_positional_param(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=1,
            column=0,
            code=Code.ODA007,
            message="Service and selector functions must use keyword-only parameters (add * before parameters)",
        )
    ]


@pytest.mark.module(
    """\
class UserService:
    def create(self, username, email):
        pass
"""
)
def test_method_without_keyword_only_params(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=2,
            column=4,
            code=Code.ODA007,
            message="Service and selector functions must use keyword-only parameters (add * before parameters)",
        )
    ]


@pytest.mark.module(
    """\
class UserService:
    @classmethod
    def create(cls, username, email):
        pass
"""
)
def test_classmethod_without_keyword_only_params(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=3,
            column=4,
            code=Code.ODA007,
            message="Service and selector functions must use keyword-only parameters (add * before parameters)",
        )
    ]


@pytest.mark.module(
    """\
async def create_user(username, email):
    pass
"""
)
def test_async_function_without_keyword_only_params(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=1,
            column=0,
            code=Code.ODA007,
            message="Service and selector functions must use keyword-only parameters (add * before parameters)",
        )
    ]


@pytest.mark.module(
    """\
def create_user(username, email):
    pass

def get_user(user_id):
    pass
"""
)
def test_multiple_violations(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert violations == [
        Violation(
            line=1,
            column=0,
            code=Code.ODA007,
            message="Service and selector functions must use keyword-only parameters (add * before parameters)",
        ),
        Violation(
            line=4,
            column=0,
            code=Code.ODA007,
            message="Service and selector functions must use keyword-only parameters (add * before parameters)",
        ),
    ]


# Tests for valid code (no violations)


@pytest.mark.module(
    """\
def create_user(*, username, email):
    pass
"""
)
def test_function_with_keyword_only_params(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
def get_user(*, user_id):
    pass
"""
)
def test_function_with_single_keyword_only_param(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
def no_params():
    pass
"""
)
def test_function_with_no_params(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
class UserService:
    def create(self, *, username, email):
        pass
"""
)
def test_method_with_keyword_only_params(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
class UserService:
    def no_params(self):
        pass
"""
)
def test_method_with_only_self(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
class UserService:
    @classmethod
    def create(cls, *, username, email):
        pass
"""
)
def test_classmethod_with_keyword_only_params(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
class UserService:
    @staticmethod
    def create(*, username, email):
        pass
"""
)
def test_staticmethod_with_keyword_only_params(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
async def create_user(*, username, email):
    pass
"""
)
def test_async_function_with_keyword_only_params(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
class UserService:
    def __init__(self, dependency):
        pass
"""
)
def test_dunder_init_not_checked(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
class UserService:
    def __str__(self):
        pass

    def __repr__(self):
        pass

    def __eq__(self, other):
        pass
"""
)
def test_dunder_methods_not_checked(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert not violations


# Tests for file/directory detection


@pytest.mark.module(
    """\
def create_user(username, email):
    pass
""",
    name="selectors",
    module="project.app",
)
def test_selectors_file_is_checked(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert len(violations) == 1


@pytest.mark.module(
    """\
def create_user(username, email):
    pass
""",
    name="user_services",
    module="project.app.services",
)
def test_services_directory_is_checked(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert len(violations) == 1


@pytest.mark.module(
    """\
def create_user(username, email):
    pass
""",
    name="user_selectors",
    module="project.app.selectors",
)
def test_selectors_directory_is_checked(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert len(violations) == 1


@pytest.mark.module(
    """\
def create_user(username, email):
    pass
""",
    name="models",
    module="project.app",
)
def test_non_service_selector_file_not_checked(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
def create_user(username, email):
    pass
""",
    name="utils",
    module="project.app.helpers",
)
def test_non_service_selector_directory_not_checked(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert not violations


# Tests for edge cases


@pytest.mark.module(
    """\
def func_with_defaults(*, username="default", email="default@example.com"):
    pass
"""
)
def test_function_with_keyword_only_params_and_defaults(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
def func_with_args_and_kwargs(*args, **kwargs):
    pass
"""
)
def test_function_with_args_and_kwargs(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    # *args and **kwargs don't require keyword-only enforcement
    assert not violations


@pytest.mark.module(
    """\
class UserService:
    def method(self, *args, **kwargs):
        pass
"""
)
def test_method_with_args_and_kwargs(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
def mixed(*, username, email="default"):
    pass
"""
)
def test_mixed_keyword_only_params_with_and_without_defaults(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert not violations


@pytest.mark.module(
    """\
def nested_function():
    def inner(param):
        pass
    return inner
"""
)
def test_nested_function_violation(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    # Only the inner function violates (outer has no params)
    assert len(violations) == 1


@pytest.mark.module(
    """\
class OuterClass:
    class InnerClass:
        def method(self, param):
            pass
"""
)
def test_nested_class_method_violation(
    checker: KeywordOnlyChecker, violations: list[Violation]
) -> None:
    assert len(violations) == 1
