from typing import Sequence

from .base import Checker, Code, Violation
from .components import ComponentIsolationChecker
from .config import ConfigChecker
from .django_orm import SelectForUpdateChecker
from .imports import RelativeImportsChecker

__all__ = [
    "Code",
    "ComponentIsolationChecker",
    "ConfigChecker",
    "RelativeImportsChecker",
    "SelectForUpdateChecker",
    "Violation",
]

ALL_CHECKERS = (
    ComponentIsolationChecker,
    ConfigChecker,
    RelativeImportsChecker,
    SelectForUpdateChecker,
)


def get_checkers(checks: list[str] | None = None) -> Sequence[type[Checker]]:
    if not checks:
        return ALL_CHECKERS
    return [cls for cls in ALL_CHECKERS if cls.slug in checks]
