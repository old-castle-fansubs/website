from pathlib import Path
from typing import Iterable, Optional, TypeVar

PROJ_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = PROJ_DIR / "templates"
STATIC_DIR = PROJ_DIR / "static"
ROOT_DIR = PROJ_DIR.parent
DATA_DIR = ROOT_DIR / "data"

TItem = TypeVar("TItem")


def first(source: Iterable[TItem]) -> Optional[TItem]:
    try:
        return next(iter(source), None)
    except StopIteration:
        return None
