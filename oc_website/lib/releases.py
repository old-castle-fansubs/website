import re
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import dateutil.parser

from oc_website.lib import jsonl
from oc_website.lib.common import DATA_DIR

RELEASES_PATH = DATA_DIR / "releases.jsonl"


@dataclass
class ReleaseFile:
    file_name: str
    file_version: int
    episode_number: str
    episode_title: str
    languages: list[str]


@dataclass
class Release:
    date: datetime
    links: list[str]
    is_visible: bool
    files: list[ReleaseFile]

    @property
    def languages(self) -> list[str]:
        return list(
            OrderedDict.fromkeys(sum((f.languages for f in self.files), []))
        )

    @property
    def btih(self) -> Optional[str]:
        for link in self.links:
            match = re.search("magnet.*btih:([0-9a-f]+)", link, flags=re.I)
            if match:
                return match.group(1)
        return None

    @property
    def is_hidden(self) -> bool:
        return not self.is_visible


def sort_links(link: str) -> int:
    for i, infix in enumerate(("magnet", "nyaa.si", "nyaa.net", "anidex")):
        if infix in link:
            return i
    return -1


def get_releases() -> list[Release]:
    releases: dict[str, Release] = {}
    for item in jsonl.loads(RELEASES_PATH.read_text(encoding="utf-8")):
        magnet = item["links"][-1]
        if magnet not in releases:
            releases[magnet] = Release(
                date=dateutil.parser.parse(item["date"]),
                links=sorted(item["links"], key=sort_links),
                is_visible=not item.get("hidden", False),
                files=[],
            )
        releases[magnet].files.append(
            ReleaseFile(
                file_name=item["file"],
                file_version=item["version"],
                episode_number=item["episode"],
                episode_title=item["title"],
                languages=item["languages"],
            )
        )
    return list(releases.values())
