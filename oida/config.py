from dataclasses import dataclass
from typing import Iterable


@dataclass
class Config:
    allowed_imports: frozenset[str] = frozenset()
    allowed_foreign_keys: frozenset[str] = frozenset()


def get_rule_for_violation(
    allowed_imports: Iterable[str], violation: str
) -> str | None:

    # Try to find a whilecard covering the violation first
    path = violation.split(".")
    while path:
        wildcard = ".".join(path[:-1]) + ".*"
        if wildcard in allowed_imports:
            return wildcard

        path = path[:-1]

    # Fall back to an explicit exclude
    return violation if violation in allowed_imports else None
