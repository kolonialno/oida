import subprocess
from itertools import zip_longest
from pathlib import Path


def run_black(value: str, *, filename: Path | None = None) -> str:
    """
    Format the given contents using black. If calling black fails the input
    will be returned unchanged instead.
    """

    command: list[str | Path] = ["black", "-c", value]
    if filename:
        command.extend(("--stdin-filename", filename))

    process = subprocess.run(command, capture_output=True, encoding="utf-8")

    return process.stdout if process.returncode == 0 else value


def path_in_glob_list(path: str, glob_list: list[str]) -> bool:
    """
    Returns True if the path is included in the provided glob list.
    """

    path_list = path.split(".")

    for glob in glob_list:
        if all(
            glob_part == "*" or path_part == glob_part or glob_part is None
            for path_part, glob_part in zip_longest(path_list, glob.split("."))
        ):
            return True

    return False
