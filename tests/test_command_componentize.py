import textwrap

import libcst as cst
import pytest

from oida.commands.componentize import AppConfigUpdater


@pytest.mark.parametrize(
    "module,expected_output",
    [
        (
            """\
            from django.apps import AppConfig

            class MyAppConfig(AppConfig):
                name = "project.app"
            """,
            """\
            from django.apps import AppConfig

            class FooAppConfig(AppConfig):
                name = "project.component.app"
                label = "app"
            """,
        ),
        (
            """\
            from django.apps import AppConfig

            class MyAppConfig(AppConfig):
                name = "project.app"
                label = "foobar"
            """,
            """\
            from django.apps import AppConfig

            class FooAppConfig(AppConfig):
                name = "project.component.app"
                label = "foobar"
            """,
        ),
    ],
    ids=[
        "add label, update class name and name",
        "leave label, update class name and name",
    ],
)
def test_add_label_and_rename_app_config(module: str, expected_output: str) -> None:
    wrapper = cst.MetadataWrapper(cst.parse_module(textwrap.dedent(module)))
    updated_module = wrapper.visit(
        AppConfigUpdater(
            class_name="FooAppConfig",
            module="project.component.app",
            default_app_label="app",
        )
    )

    expected_module = cst.parse_module(textwrap.dedent(expected_output))
    assert updated_module.deep_equals(expected_module)
