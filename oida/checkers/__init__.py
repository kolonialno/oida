from typing import Sequence

from .apps import AppIsolationChecker
from .base import Checker
from .imports import RelativeImportsChecker

__all__ = [
    "AppIsolationChecker",
    "RelativeImportsChecker",
]

ALL_CHECKERS = (
    AppIsolationChecker,
    RelativeImportsChecker,
)


def get_checkers(checks: list[str] | None = None) -> Sequence[type[Checker]]:
    if not checks:
        return ALL_CHECKERS
    return [cls for cls in ALL_CHECKERS if cls.slug in checks]
