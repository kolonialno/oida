from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(slots=True)
class Violation:
    file: Path
    line: int
    column: int
    message: str


class Reporter(Protocol):
    def report_violation(
        self, file: Path, line: int, column: int, message: str
    ) -> None:
        raise NotImplementedError


class StdoutReporter:
    def __init__(self) -> None:
        self.has_violations = False

    def report_violation(
        self, file: Path, line: int, column: int, message: str
    ) -> None:
        print(f"{file}:{line}:{column}: {message}")
        self.has_violations = True

    def print_summary(self) -> None:
        if self.has_violations:
            print("Oida, looks like there's some issues here!")
        else:
            print("Great work, no problems found ✋")
