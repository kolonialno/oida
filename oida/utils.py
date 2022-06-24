import subprocess
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
