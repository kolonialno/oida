from typing import TypedDict


class SubserviceConfig(TypedDict, total=False):
    database: str
    apps: list[str]
