import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Optional, Union

import libcst as cst
from libcst import BaseStatement, Decorator, FlattenSentinel, RemovalSentinel
from libcst import matchers as m
from libcst.codemod import (
    CodemodContext,
    ContextAwareTransformer,
    parallel_exec_transform_with_prettyprint,
)
from libcst.codemod.commands.rename import RenameCommand as BaseRenameCommand
from libcst.metadata import QualifiedNameProvider

from ..discovery import find_root_module, get_module
from ..utils import run_black


def componentize_app(old_path: Path, new_path: Path) -> None:
    """
    Move an app into a component. This will move the code and update any
    imports in the project.
    """

    root_module = find_root_module(old_path.resolve())
    if find_root_module(new_path.resolve()) != root_module:
        print(f"root module of old path: {root_module}")
        print(f"root module of new path: {find_root_module(new_path.resolve())}")
        sys.exit("Cannot move app to a different project")

    print("Creating target directory")
    new_path.mkdir(parents=True, exist_ok=True)

    print("Moving to new directory")
    for path in old_path.iterdir():
        if path == new_path:
            continue

        path.rename(new_path / path.name)

    print("Ensuring all __init__.py files exist")
    path = new_path.resolve()
    while path != root_module:
        init_py_file_path = path / "__init__.py"
        init_py_file_path.touch(exist_ok=True)
        path = path.parent

    # Remove the source directory if it's empty now
    if not old_path.iterdir():
        print("Remvoing old app directory")
        old_path.unlink()

    print("Updating imports from moved app (might take a while)")
    update_imports(root_module, old_path, new_path)

    print("Updating app config")
    update_or_create_app_config(old_path, new_path)

    print("Updating celery task naming")
    update_celery_task_names(root_module, old_path, new_path)

    if shutil.which("isort"):
        print("Running isort")
        subprocess.check_call(["isort", root_module])
    if shutil.which("black"):
        print("Running black")
        subprocess.check_call(["black", root_module])


class RenameCommand(BaseRenameCommand):
    def leave_SimpleString(
        self, original_node: cst.SimpleString, updated_node: cst.SimpleString
    ) -> cst.SimpleString:
        if isinstance(updated_node.evaluated_value, str) and (
            updated_node.evaluated_value == self.old_name
            or updated_node.evaluated_value.startswith(f"{self.old_name}.")
        ):
            return updated_node.with_changes(
                value=updated_node.value.replace(self.old_name, self.new_name)
            )
        return updated_node


def update_imports(root_module: Path, old_path: Path, new_path: Path) -> None:
    """
    Update imports in the given module
    """

    # Rewrite imports from the moved module
    old_module = get_module(old_path)
    new_module = get_module(new_path)

    context = CodemodContext()
    codemod = RenameCommand(context, old_module, new_module)
    files = [str(path) for path in root_module.rglob("*.py")]

    parallel_exec_transform_with_prettyprint(
        codemod, files=files, repo_root=str(root_module)
    )


class AppConfigUpdater(cst.CSTTransformer):
    """
    This class is responsible for modifying the AppConfig of the app we're
    moving. It will do the following:

     - Update the name of the class to match the new component name
     - Update the name attribute on the class to match the new module name
     - Add a label attribute if one does not already exist
    """

    METADATA_DEPENDENCIES = (QualifiedNameProvider,)

    def __init__(self, class_name: str, module: str, default_app_label: str) -> None:
        self.class_name = class_name
        self.module = module
        self.default_app_label = default_app_label

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:

        # Check if this class is a subclass of AppConfig. If it's not we don't
        # want to touch it
        if not any(
            qualname.name == "django.apps.AppConfig"
            for base in original_node.bases
            for qualname in self.get_metadata(QualifiedNameProvider, base.value)
        ):
            return updated_node

        # Matchers for name and label attributes. Does not support typed expressions
        app_name_matcher = m.SimpleStatementLine(
            body=[m.Assign(targets=[m.AssignTarget(m.Name("name"))])]
        )
        app_label_matcher = m.SimpleStatementLine(
            body=[m.Assign(targets=[m.AssignTarget(m.Name("label"))])]
        )

        # Replace the old name statement with a new one, and copy the rest of
        # the class body
        updated_body = [
            statement
            if not m.matches(statement, app_name_matcher)
            else cst.parse_statement(f'name = "{self.module}"')
            for statement in updated_node.body.body
        ]

        # If there's no 'label = ...' statement in the body add one
        if not any(
            m.matches(statement, app_label_matcher) for statement in updated_body
        ):
            updated_body.append(
                cst.parse_statement(f'label = "{self.default_app_label}"')
            )

        return updated_node.with_changes(
            name=cst.Name(self.class_name),
            body=updated_node.body.with_changes(body=updated_body),
        )


def update_or_create_app_config(old_path: Path, new_path: Path) -> None:
    old_module = get_module(old_path)
    new_module = get_module(new_path)
    default_app_label = old_module.rsplit(".", 1)[-1]
    class_name = "".join(
        (
            new_path.parent.name.title().replace("_", ""),
            new_path.name.title().replace("_", ""),
            "Config",
        )
    )

    apps_py_path = new_path / "apps.py"
    if not apps_py_path.exists():
        apps_py_path.write_text(
            textwrap.dedent(
                f"""\
                from django.apps import AppConfig


                class {class_name}(AppConfig):
                    name = "{new_module}"
                    label = "{default_app_label}"
                """
            )
        )
    else:
        module = cst.MetadataWrapper(cst.parse_module(apps_py_path.read_text()))
        updated_module = module.visit(
            AppConfigUpdater(class_name, new_module, default_app_label)
        )
        apps_py_path.write_text(run_black(updated_module.code))


class CeleryTaskNameUpdater(ContextAwareTransformer):
    """
    This updater searches for Celery tasks defined with the @app.task decorator, where
    the name of the task is implicitly set. This name includes the folder structure of the Django app.
    Because we need to keep the name the same if we move apps into components, we need to set the name
    explicitly to the original name, i.e. without the component name.
    It also checks whether the name has already been explicitly set, if so the name is NOT changed.
    """

    def __init__(
        self, context: CodemodContext, old_module: str, new_module: str
    ) -> None:
        super().__init__(context=context)
        self.old_module = old_module
        self.new_module = new_module
        self.in_app: int = 0
        self.function_name: str | None = None

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        if self.context.full_module_name is not None:
            current_module_name_list = self.context.full_module_name.split(".")
            new_module_name_list = self.new_module.split(".")
            # The full module name is in the form: product_availability.core.services.data.supply
            # while the module we are changing is of the form: tienda.product_availability.core
            # We, therefore, need to check if the last two (string) components of the name of the
            # new module are equal to the first two (string) components of the name of the module
            # currently being processed. If we do not do this test - all tasks in the project
            # (e.g. tienda) will be prepended with the component name, which is wrong.
            if (
                len(current_module_name_list) >= 2
                and len(new_module_name_list) >= 2
                and current_module_name_list[:2] == new_module_name_list[-2:]
            ):
                return tree.visit(self)
        return tree

    def visit_Decorator(self, node: cst.Decorator) -> Optional[bool]:
        # Determine if the decorator is the @app.task decorator
        if m.matches(
            node,
            m.Decorator(m.Call(m.Attribute(value=m.Name("app"), attr=m.Name("task")))),
        ):
            self.in_app += 1
        return super().visit_Decorator(node)

    def leave_Decorator(
        self, original_node: cst.Decorator, updated_node: cst.Decorator
    ) -> Union[Decorator, FlattenSentinel[Decorator], RemovalSentinel]:
        # Determine if the decorator is the @app.task decorator
        if m.matches(
            original_node,
            m.Decorator(m.Call(m.Attribute(value=m.Name("app"), attr=m.Name("task")))),
        ):
            self.in_app -= 1
        return updated_node

    def leave_Call(
        self, original_node: cst.Call, updated_node: cst.Call
    ) -> cst.BaseExpression:
        # self.in_app > 0 if we are in an @app.task decorator
        if self.in_app > 0:
            # Test if the name of the task is not explicitly set
            if not m.matches(
                original_node,
                m.Call(
                    args=[m.ZeroOrMore(), m.Arg(keyword=m.Name("name")), m.ZeroOrMore()]
                ),
            ):
                arguments = original_node.args
                # The implicit name of the task is the path to the old module concatenated with the function name.
                task_name = f'"{self.old_module}.{self.function_name}"'
                arguments = (  # type: ignore
                    cst.Arg(
                        keyword=cst.Name("name"),
                        value=cst.SimpleString(value=task_name),
                        # Equal and comma are not strictly necessary - the code would be functional without these.
                        # They are needed however to comply with coding conventions and pass the unit test.
                        equal=cst.AssignEqual(
                            whitespace_before=cst.SimpleWhitespace(value=""),
                            whitespace_after=cst.SimpleWhitespace(value=""),
                        ),
                        comma=cst.Comma(
                            whitespace_before=cst.SimpleWhitespace(value=""),
                            whitespace_after=cst.ParenthesizedWhitespace(
                                first_line=cst.TrailingWhitespace(
                                    whitespace=cst.SimpleWhitespace(value=""),
                                    comment=None,
                                    newline=cst.Newline(value=None),
                                ),
                                empty_lines=[],
                                indent=True,
                                last_line=cst.SimpleWhitespace(value="    "),
                            ),
                        ),
                    ),
                ) + arguments
                new_node = updated_node.with_changes(args=arguments)
                return new_node
        return updated_node

    def visit_FunctionDef(self, node: cst.FunctionDef) -> Optional[bool]:
        if m.matches(
            node,
            m.FunctionDef(
                decorators=[
                    m.ZeroOrMore(),
                    m.Decorator(
                        m.Call(m.Attribute(value=m.Name("app"), attr=m.Name("task")))
                    ),
                    m.ZeroOrMore(),
                ]
            ),
        ):
            # We need the name of the function to recreate the implicit task name.
            self.function_name = node.name.value
        return super().visit_FunctionDef(node)

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> Union[BaseStatement, FlattenSentinel[BaseStatement], RemovalSentinel]:
        self.function_name = None
        return updated_node


def update_celery_task_names(root_module: Path, old_path: Path, new_path: Path) -> None:
    old_module = get_module(old_path)
    new_module = get_module(new_path)

    files = [str(path) for path in root_module.rglob("*.py")]
    context = CodemodContext()
    codemod = CeleryTaskNameUpdater(context, old_module, new_module)

    parallel_exec_transform_with_prettyprint(
        codemod, files=files, repo_root=str(root_module)
    )
