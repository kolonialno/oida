from dataclasses import dataclass


@dataclass
class Config:
    allowed_imports: tuple[str, ...] | None = None
    allowed_foreign_keys: tuple[str, ...] | None = None
