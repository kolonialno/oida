from pathlib import Path


class Component:
    def __init__(
        self, name: str, path: Path, apps: list[Path], has_public_api: bool
    ) -> None:
        self.name = name
        self.path = path
        self.apps = apps
        self.has_public_api = has_public_api

    def __str__(self) -> str:
        return f"Component [name={self.name}, path={self.path}, apps={self.apps}, publicAPI:{self.has_public_api}]"
