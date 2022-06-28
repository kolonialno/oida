import os
import subprocess
import sys
import textwrap
from pathlib import Path

import libcst as cst
from libcst import matchers as m
from libcst.metadata import QualifiedNameProvider

from ..discovery import find_project_root, get_module
from ..utils import run_black


def componentize_app(old_path: Path, new_path: Path) -> None:
    """
    Move an app into a component. This will move the code and update any
    imports in the project.
    """

    project_root = find_project_root(old_path.resolve())
    if find_project_root(new_path.resolve()) != project_root:
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
    while path != project_root:
        init_py_file_path = path / "__init__.py"
        init_py_file_path.touch(exist_ok=True)
        path = path.parent

    # Remove the source directory if it's empty now
    if not old_path.iterdir():
        print("Remvoing old app directory")
        old_path.unlink()

    print("Updating imports from moved app")
    update_imports(project_root, old_path, new_path)

    print("Updating app label")
    update_or_create_app_config(old_path, new_path)


def update_imports(project_root: Path, old_path: Path, new_path: Path) -> None:
    """
    Update imports in the given module
    """

    # Locate the project source dir (one level below project root)
    source_dir = new_path.resolve()
    while source_dir.parent != project_root:
        source_dir = source_dir.parent

    # Rewrite imports from the moved module
    old_module = get_module(old_path)
    new_module = get_module(new_path)

    subprocess.run(
        [
            sys.executable,
            "-m",
            "libcst.tool",
            "codemod",
            "rename.RenameCommand",
            "--old_name",
            old_module,
            "--new_name",
            new_module,
            source_dir,
        ],
        check=True,
        capture_output=True,
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
