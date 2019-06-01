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
