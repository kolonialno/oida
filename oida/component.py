
from pathlib import Path


class Component:

    def __init__(
        self, name: str, path: Path, apps: list[str], hasPublicAPI: bool
    ) -> None:
        self.name = name
        self.path = path
        self.apps = apps
        self.has_public_API = hasPublicAPI

    def __str__(self):
        return f"Component [name={self.name}, path={self.path}, apps={self.apps}, publicAPI:{self.has_public_API}]"