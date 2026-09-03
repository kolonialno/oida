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


@pytest.mark.pyproject_toml(
    """\
    [tool.oida]
    record_modules = ["records", "schemas"]
    record_base_classes = ["Body", "CamelModel"]
    record_build_methods = ["build", "serialize"]
    """
)
def test_project_config_record_settings(project_config: ProjectConfig) -> None:
    assert project_config.record_modules == ["records", "schemas"]
    assert project_config.record_base_classes == ["Body", "CamelModel"]
    assert project_config.record_build_methods == ["build", "serialize"]


def test_project_config_record_defaults(project_config: ProjectConfig) -> None:
    assert project_config.record_modules == ["records"]
    assert project_config.record_base_classes == []
    assert project_config.record_build_methods == ["build", "build_*"]
