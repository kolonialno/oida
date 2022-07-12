from typing import Sequence

from .base import Checker, Code, Violation
from .components import ComponentIsolationChecker
from .config import ConfigChecker
from .imports import RelativeImportsChecker
from .models import ComponentModelIsolationChecker

__all__ = [
    "Code",
    "ComponentIsolationChecker",
    "ComponentModelIsolationChecker",
    "ConfigChecker",
    "RelativeImportsChecker",
    "Violation",
]

ALL_CHECKERS = (
    ComponentIsolationChecker,
    ComponentModelIsolationChecker,
    ConfigChecker,
    RelativeImportsChecker,
)


def get_checkers(checks: list[str] | None = None) -> Sequence[type[Checker]]:
    if not checks:
        return ALL_CHECKERS
    return [cls for cls in ALL_CHECKERS if cls.slug in checks]
