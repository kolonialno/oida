import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import libcst as cst
from libcst import matchers as m
from libcst.codemod import CodemodContext, parallel_exec_transform_with_prettyprint
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
