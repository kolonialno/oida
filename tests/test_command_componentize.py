import textwrap

import libcst as cst
import pytest

from oida.commands.componentize import AppConfigUpdater, CeleryTaskNameUpdater


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
            def publish_tracking_data_to_pubsub(
                topic: str, msg: bytes | dict, attributes: dict[str, str] | None = None
            ) -> None:
                pass
            """,
            """\
            @app.task(
                name="project.app.tasks.publish_tracking_data_to_pubsub",
                max_retries=10,
                default_retry_delay=60,
                queue=settings.TASK_QUEUE_LOW_LATENCY_TRACKING,
            )
            def publish_tracking_data_to_pubsub(
                topic: str, msg: bytes | dict, attributes: dict[str, str] | None = None
            ) -> None:
                pass
            """,
        ),
    ],
    ids=[
        "add label, update class name and name",
    ],
)
def testapp_celery_task_name_updater(module: str, expected_output: str) -> None:
    wrapper = cst.MetadataWrapper(cst.parse_module(textwrap.dedent(module)))
    updated_module = wrapper.visit(
        CeleryTaskNameUpdater(
            old_module="project.app.tasks",
            new_module="project.component.app.tasks",
        )
    )

    expected_module = cst.parse_module(textwrap.dedent(expected_output))
    assert updated_module.deep_equals(expected_module)
