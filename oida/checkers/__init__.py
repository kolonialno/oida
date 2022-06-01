from typing import Sequence

from .base import Checker
from .components import ComponentIsolationChecker
from .config import ConfigChecker
from .imports import RelativeImportsChecker

__all__ = [
    "ComponentIsolationChecker",
    "ConfigChecker",
    "RelativeImportsChecker",
]

ALL_CHECKERS = (
    ComponentIsolationChecker,
    ConfigChecker,
    RelativeImportsChecker,
)


def get_checkers(checks: list[str] | None = None) -> Sequence[type[Checker]]:
    if not checks:
        return ALL_CHECKERS
    return [cls for cls in ALL_CHECKERS if cls.slug in checks]
