from .base import Checker
from .imports import CheckRelativeImports


def get_checkers() -> list[Checker]:
    return [
        CheckRelativeImports(),
    ]
