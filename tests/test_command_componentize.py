import textwrap

import libcst as cst
import pytest
from libcst.codemod import CodemodContext

from oida.commands.componentize import AppConfigUpdater, CeleryTaskNameUpdater
from oida.utils import run_black


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
def testapp_config_updater(module: str, expected_output: str) -> None:
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


@pytest.mark.parametrize(
    "module,expected_output",
    [
        (
            """\
            @app.task(
                max_retries=10,
                default_retry_delay=60,
                queue=settings.TASK_QUEUE_LOW_LATENCY_TRACKING,
            )
            @app.some.other.decorator(
                foo="bar",
            )
            def some_function(
                topic: str, msg: bytes | dict, attributes: dict[str, str] | None = None
            ) -> None:
                pass

            @app.some.other.decorator(
                foo="bar",
            )
            @app.task(
                name="other_dir.some_other_function",
                max_retries=10,
                default_retry_delay=60,
                queue=settings.TASK_QUEUE_LOW_LATENCY_TRACKING,
            )
            def some_other_function(
                topic: str, msg: bytes | dict, attributes: dict[str, str] | None = None
            ) -> None:
                pass
            """,
            """\
            @app.task(
                name="project.app.tasks.some_function",
                max_retries=10,
                default_retry_delay=60,
                queue=settings.TASK_QUEUE_LOW_LATENCY_TRACKING,
            )
            @app.some.other.decorator(
                foo="bar",
            )
            def some_function(
                topic: str, msg: bytes | dict, attributes: dict[str, str] | None = None
            ) -> None:
                pass

            @app.some.other.decorator(
                foo="bar",
            )
            @app.task(
                name="other_dir.some_other_function",
                max_retries=10,
                default_retry_delay=60,
                queue=settings.TASK_QUEUE_LOW_LATENCY_TRACKING,
            )
            def some_other_function(
                topic: str, msg: bytes | dict, attributes: dict[str, str] | None = None
            ) -> None:
                pass
            """,
        ),
    ],
    ids=[
        "add task name to decorator",
    ],
)
def testapp_celery_task_name_updater(module: str, expected_output: str) -> None:
    source_tree = cst.parse_module(textwrap.dedent(module))
    context = CodemodContext()
    transformer = CeleryTaskNameUpdater(
        context=context,
        module_name="project.app.tasks",
    )
    updated_module_code = run_black(source_tree.visit(transformer).code)
    expected_module_code = run_black(
        cst.parse_module(textwrap.dedent(expected_output)).code
    )
    assert updated_module_code == expected_module_code
