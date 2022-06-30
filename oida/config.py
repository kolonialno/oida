from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Iterable

if sys.version_info >= (3, 11):
    from tomllib import loads as load_toml
else:
    from tomli import loads as load_toml


@dataclass
class ProjectConfig:
    ignored_modules: list[str] = field(default_factory=list)

    @classmethod
    def from_pyproject_toml(cls, pyproject_toml: str) -> ProjectConfig:
        raw = load_toml(pyproject_toml)
        data = raw.get("tool", {}).get("oida", {})
        return cls(**data)

    def is_ignored(self, module: str | None, name: str) -> bool:
        path = (module or "").split(".") + [name]

        for ignore in self.ignored_modules:
            if all(
                name == "*" or len(path) < i or name == path[i]
                for i, name in enumerate(ignore.split("."))
            ):
                return True

        return False


@dataclass
class ComponentConfig:
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
