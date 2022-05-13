from .base import Checker
from .imports import CheckRelativeImports, CheckServiceAndSelectorImports


def get_checkers() -> list[Checker]:
    return [
        CheckRelativeImports(),
        CheckServiceAndSelectorImports(),
    ]
