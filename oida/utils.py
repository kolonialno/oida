import re
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


def parse_noida_comment(line: str) -> set[str] | None:
    """
    Parse a noida comment from a line of source code.

    Returns:
        - None if no noida comment is found
        - Empty set if "# noida" (ignore all violations)
        - Set of specific codes if "# noida: ODA001,ODA002" (ignore specific codes)

    Examples:
        >>> parse_noida_comment("x = 1  # noida")
        set()
        >>> parse_noida_comment("x = 1  # noida: ODA005")
        {'ODA005'}
        >>> parse_noida_comment("x = 1  # noida: ODA005, ODA001")
        {'ODA005', 'ODA001'}
        >>> parse_noida_comment("x = 1  # regular comment")
        None
    """
    # Match "# noida" optionally followed by ": CODE1, CODE2, ..."
    # Case-insensitive matching for "noida"
    match = re.search(r"#\s*noida(?::\s*([A-Z0-9,\s]+))?", line, re.IGNORECASE)

    if not match:
        return None

    codes_str = match.group(1)
    if not codes_str:
        # "# noida" without specific codes - ignore all
        return set()

    # Parse the comma-separated list of codes
    codes = {code.strip() for code in codes_str.split(",") if code.strip()}
    return codes
