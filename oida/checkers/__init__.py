from .apps import AppIsolationChecker
from .base import Checker
from .imports import RelativeImportsChecker

__all__ = [
    "AppIsolationChecker",
    "RelativeImportsChecker",
]


def get_checkers() -> list[Checker]:
    return [
        AppIsolationChecker(),
        RelativeImportsChecker(),
    ]
