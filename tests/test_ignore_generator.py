from pathlib import Path

import pytest

from oida.config_generator import collect_violations

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
    print(violations)
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
