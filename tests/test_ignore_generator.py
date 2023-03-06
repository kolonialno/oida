import textwrap
from pathlib import Path

import libcst as cst
import pytest

from oida.config_generator import (
    collect_violations,
    update_allowed_imports,
    update_component_config,
)
from oida.utils import run_black

# Define a test project with a component and some files for the test to run
# against. These files will be created as defined here unless overridden by a
# mark on the test function.
pytestmark = pytest.mark.project_files(
    {
        "project/__init__.py": "",
        "project/component/__init__.py": "",
        "project/component/confcomponent.py": "",
        "project/component/app/__init__.py": "",
        "project/component/app/foo.py": """
            from project.other.app.services import private, also_private
            private()
            also_private()
            """,
        "project/component/app/bar.py": """
            from project.other.app.services import private
            private()
            """,
        "project/component/app/baz.py": """
            from project.other.app.selectors import private
            private()
            """,
    }
)


def test_project_path_fixture(project_path: Path) -> None:
    assert (project_path / "project").is_dir()
    with open(project_path / "project/component/confcomponent.py") as f:
        assert f.read() == ""


@pytest.mark.project_files({"project/component/confcomponent.py": "OVERRIDE = True"})
def test_override_file_with_marker(project_path: Path) -> None:
    with open(project_path / "project/component/confcomponent.py") as f:
        assert f.read() == "OVERRIDE = True"


@pytest.mark.project_files(
    {
        "project/other/__init__.py": "",
        "project/other/app/__init__.py": "",
        "project/other/app/services.py": """
            from project.component.app.services import private
            private()
            """,
    }
)
def test_collect_violations(project_path: Path) -> None:
    violations = collect_violations(project_path / "project")
    assert violations == {
        (project_path / "project" / "component"): {
            "project.other.app.services.private",
            "project.other.app.services.also_private",
            "project.other.app.selectors.private",
        },
        (project_path / "project" / "other"): {
            "project.component.app.services.private",
        },
    }


@pytest.mark.project_files(
    {
        "project/other/__init__.py": "",
        "project/other/app/__init__.py": "",
        "project/other/app/services.py": """
            from project.component.app.services import private
            private()
        """,
        "project/other/app/tests/__init__.py": "",
        "project/other/app/tests/test_methods.py": """
            from project.component.app.tests.utils import create_util
            create_util()
        """,
    }
)
def test_collect_violations_excluded_path(project_path: Path) -> None:
    violations = collect_violations(project_path / "project", Path("tests"))
    assert violations == {
        (project_path / "project" / "component"): {
            "project.other.app.services.private",
            "project.other.app.services.also_private",
            "project.other.app.selectors.private",
        },
        (project_path / "project" / "other"): {
            "project.component.app.services.private",
        },
    }


@pytest.mark.parametrize(
    "current,violations,expected",
    [
        (set(), set(), set()),
        ({"not.in.use"}, set(), set()),
        (set(), {"this.is.a.violation"}, {"this.is.a.violation"}),
        ({"this.is.a.*"}, {"this.is.a.violation"}, {"this.is.a.*"}),
        (
            {"this.is.a.*", "this.is.a.violation"},
            {"this.is.a.violation"},
            {"this.is.a.*"},
        ),
        (
            {},
            {"this.is.a.violation", "this.is.also.a.violation"},
            {"this.is.a.violation", "this.is.also.a.violation"},
        ),
        (
            {"this.*"},
            {"this.is.a.violation", "this.is.also.a.violation"},
            {"this.*"},
        ),
    ],
    ids=[
        "empty",
        "remove-unused",
        "add-new-violation",
        "use-wildcard",
        "remove-duplicated-by-wildcard",
        "multiple-violations",
        "multiple-violations-wildcard",
    ],
)
def test_update_allowed_imports(
    current: set[str], violations: set[str], expected: set[str]
) -> None:
    assert update_allowed_imports(current, violations) == expected


@pytest.mark.parametrize(
    "config,violations,expected_output",
    [
        ("", set(), ""),
        ("", {"this.*"}, 'ALLOWED_IMPORTS: set[str] = {"this.*"}\n'),
        (
            "ALLOWED_IMPORTS: set[str] = set()",
            {"this.*"},
            'ALLOWED_IMPORTS: set[str] = {"this.*"}\n',
        ),
        (
            """\
            ALLOWED_IMPORTS: set[str] = {
                # This is a comment
                "foo",
            }
            """,
            {"foo", "this.*"},
            """\
            ALLOWED_IMPORTS: set[str] = {
                # This is a comment
                "foo",
                "this.*",
            }
            """,
        ),
        ('ALLOWED_IMPORTS: set[str] = {"this.*"}', set(), ""),
    ],
    ids=[
        "empty",
        "add-violation-no-constan-no-constantt",
        "add-violation-to-empty-set",
        "should-keep-comments",
        "remove-unused-config",
    ],
)
def test_update_config(
    config: str,
    violations: set[str],
    expected_output: str,
) -> None:
    node = cst.parse_module(textwrap.dedent(config))
    updated_config = update_component_config(node, allowed_imports=violations)
    assert run_black(updated_config.code) == textwrap.dedent(expected_output)
