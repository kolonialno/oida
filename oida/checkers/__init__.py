from .base import Checker
from .imports import RelativeImportsChecker, ServiceAndSelectorImportsChecker

__all__ = ["RelativeImportsChecker", "ServiceAndSelectorImportsChecker"]


def get_checkers() -> list[Checker]:
    return [
        RelativeImportsChecker(),
        ServiceAndSelectorImportsChecker(),
    ]
