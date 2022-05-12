from pathlib import Path
from typing import Iterable

from .state import Module


def get_package(path: Path) -> str:
    """
    Given a path to a python module (directory or file), find it's absolute
    module name.
    """

    names: list[str] = [path.stem] if path.is_dir() else []
    while path.parent and (path.parent / "__init__.py").exists():
        names.insert(0, path.parent.stem)
        path = path.parent

    return ".".join(names)


def check_directory(path: Path, package: str | None = None) -> Iterable[Module]:
    """
    Given a path to a directory, find and load all modules in that directory.
    """

    if not (path / "__init__.py").exists():
        for child in path.iterdir():
            if child.stem.startswith("."):
                continue
            if child.is_dir():
                yield from check_directory(child)
            elif child.suffix in (".py", ".pyi"):
                yield Module(package=None, name=child.stem, path=child)
    else:
        package = f"{package}.{path.stem}" if package else get_package(path)
        for child in path.iterdir():
            if child.stem.startswith("."):
                continue
            if child.is_dir():
                yield from check_directory(child, package)
            elif child.suffix in (".py", ".pyi"):
                yield check_file(child, package)


def check_file(path: Path, package: str | None = None) -> Module:

    if package is None:
        package = get_package(path)

    return Module(
        package=package, name="" if path.stem == "__init__" else path.stem, path=path
    )


def find_modules(paths: tuple[Path, ...]) -> Iterable[Module]:
    """
    Recursively check modules, starting at the given path.
    """

    for path in paths:
        if path.is_dir():
            yield from check_directory(path)
        elif path.suffix in (".py", ".pyi"):
            yield check_file(path)
