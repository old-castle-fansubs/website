import json
import typing as T
from dataclasses import dataclass
from datetime import datetime

import dateutil.parser

from oc_website.lib.common import DATA_DIR

RELEASES_PATH = DATA_DIR / "releases.json"


@dataclass
class Release:
    date: datetime
    file_name: str
    file_version: int
    episode_number: str
    episode_title: str
    links: T.List[str]
    is_visible: bool

    def get_link(self, text: str) -> T.Optional[str]:
        for link in self.links:
            if text in link:
                return link
        return None

    @property
    def is_hidden(self) -> bool:
        return not self.is_visible


def get_releases() -> T.Iterable[Release]:
    return [
        Release(
            date=dateutil.parser.parse(item["date"]),
            file_name=item["file"],
            file_version=item["version"],
            episode_number=item["episode"],
            episode_title=item["title"],
            links=item["links"],
            is_visible=not item.get("hidden", False),
        )
        for item in json.loads(RELEASES_PATH.read_text(encoding="utf-8"))
    ]
