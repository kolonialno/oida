from .apps import AppIsolationChecker
from .base import Checker
from .config import SubserviceConfigChecker
from .imports import RelativeImportsChecker

__all__ = [
    "AppIsolationChecker",
    "RelativeImportsChecker",
    "SubserviceConfigChecker",
]


def get_checkers() -> list[Checker]:
    return [
        AppIsolationChecker(),
        RelativeImportsChecker(),
        SubserviceConfigChecker(),
    ]
