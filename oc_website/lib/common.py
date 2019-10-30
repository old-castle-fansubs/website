import typing as T
from pathlib import Path

PROJ_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = PROJ_DIR / "templates"
ROOT_DIR = PROJ_DIR.parent
DATA_DIR = ROOT_DIR / "data"
STATIC_DIR = ROOT_DIR / "static"

TItem = T.TypeVar("TItem")


def first(source: T.Iterable[TItem]) -> T.Optional[TItem]:
    try:
        return next(source)
    except StopIteration:
        return None


def format_size(num, binary=False):
    suffix = "iB" if binary else "B"
    div = 1024 if binary else 1000
    for prefix in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < div:
            return f"{num:.1f} {prefix}{suffix}"
        num /= div
    return f"{num:.1f} Y{suffix}"
