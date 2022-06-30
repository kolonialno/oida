import pytest

from oida.config import ProjectConfig


@pytest.mark.pyproject_toml(
    """\
    [tool.oida]
    ignored_modules = ["foo.*.tests"]
    """
)
def test_project_config_from_mark(project_config: ProjectConfig) -> None:
    assert project_config.ignored_modules == ["foo.*.tests"]


def test_project_config_no_mark(project_config: ProjectConfig) -> None:
    assert project_config.ignored_modules == []
