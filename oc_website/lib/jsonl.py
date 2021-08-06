import json
from typing import Any, Iterable, Union


def loads(source: Union[str, Iterable[str]]) -> list[Any]:
    lines: Iterable[str]
    if isinstance(source, str):
        lines = source.splitlines()
    else:
        lines = source
    return [json.loads(line) for line in lines if line]


def dumps(items: list[Any]) -> str:
    return "\n".join(json.dumps(item) for item in items) + "\n"
