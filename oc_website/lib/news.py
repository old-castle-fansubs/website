import typing as T
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import arrow

from oc_website.lib.common import ROOT_DIR


@dataclass
class News:
    date: datetime
    title: str
    author: str
    content: str
    path: Path


def get_news() -> T.Iterable[News]:
    news_dir = ROOT_DIR / "html" / "news"
    for news_path in news_dir.iterdir():
        with news_path.open("r", encoding="utf-8") as handle:
            date = arrow.get(handle.readline())
            title = handle.readline().strip()
            author = handle.readline().strip()
            if handle.readline().strip():
                raise ValueError(
                    "Expected empty line in news " + news_path.name
                )
            content = handle.read()
        yield News(date, title, author, content, news_path)
