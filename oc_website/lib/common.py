import typing as T
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent

TItem = T.TypeVar("TItem")


def first(source: T.Iterable[TItem]) -> T.Optional[TItem]:
    try:
        return next(source)
    except StopIteration:
        return None
