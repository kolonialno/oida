import ast
import functools
from pathlib import Path
from typing import Iterable

from .checkers import ConfigChecker
from .config import ComponentConfig, ProjectConfig
from .module import Module


def get_module(path: Path) -> str:
    """
    Given a path to a python module (directory or file), find it's absolute
    module name.
    """

    names: list[str] = [path.stem] if path.is_dir() else []
    while (path.parent / "__init__.py").exists():
        names.insert(0, path.parent.stem)
        path = path.parent

    return ".".join(names)


@functools.lru_cache
def get_project_config(path: Path) -> ProjectConfig:

    pyproject_toml_path = path / "pyproject.toml"

    if pyproject_toml_path.exists():
        return ProjectConfig.from_pyproject_toml(pyproject_toml_path.read_text())

    if path.parent != path:
        return get_project_config(path.parent)

    # Fall back to returning an empty config
    return ProjectConfig()


@functools.lru_cache
def get_component_config(path: Path) -> ComponentConfig | None:
    """
    Given a path to a directory find the relevant project config.
    """

    if not (path / "__init__.py").exists():
        return None

    if (conf_path := path / "confcomponent.py") and conf_path.exists():
        return load_component_config(conf_path)

    return get_component_config(path.parent)


@functools.lru_cache(maxsize=None)
def load_component_config(path: Path) -> ComponentConfig:
    """
    Load component config from a file.
    """

    module = get_module(path.parent)
    name = path.stem

    checker = ConfigChecker(
        module=module, name=name, component_config=None, project_config=ProjectConfig()
    )
    with open(path) as f:
        checker.visit(ast.parse(f.read(), str(path)))
    return checker.parsed_config


def sort_paths(paths: Iterable[Path]) -> list[Path]:
    sorted_paths: list[Path] = []

    for path in paths:
        if path.stem.startswith("."):
            continue

        if not path.is_dir() and path.name == "confservice.py":
            sorted_paths.insert(0, path)
        elif path.is_dir():
            sorted_paths.append(path)
        elif path.suffix in (".py", ".pyi"):
            sorted_paths.insert(1, path)

    return sorted_paths


def check_directory(path: Path, module: str | None = None) -> Iterable[Module]:
    """
    Given a path to a directory, find and load all modules in that directory.
    """

    if not (path / "__init__.py").exists():
        for child in sort_paths(path.iterdir()):
            if child.is_dir():
                yield from check_directory(child)
            else:
                yield Module(module=None, name=child.stem, path=child)
    else:
        module = f"{module}.{path.stem}" if module else get_module(path)
        for child in sort_paths(path.iterdir()):
            if child.is_dir():
                yield from check_directory(child, module)
            else:
                yield check_file(child, module)


def check_file(path: Path, module: str | None = None) -> Module:

    if module is None:
        module = get_module(path)

    return Module(
        module=module, name="" if path.stem == "__init__" else path.stem, path=path
    )


def find_modules(*paths: Path) -> Iterable[Module]:
    """
    Recursively check modules, starting at the given path.
    """

    for path in paths:
        if path.is_dir():
            yield from check_directory(path)
        elif path.suffix in (".py", ".pyi"):
            yield check_file(path)


def find_root_module(path: Path) -> Path:
    """
    Find the top-level module, given a path to a file or directory
    """

    if not (path.parent / "__init__.py").exists():
        return path

    return find_root_module(path.parent)
