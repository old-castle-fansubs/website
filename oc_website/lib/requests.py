import dataclasses
import re
from datetime import datetime
from typing import Any, Iterable, Optional

import dateutil.parser

from oc_website.lib import jsonl
from oc_website.lib.common import DATA_DIR

REQUESTS_PATH = DATA_DIR / "requests.jsonl"


@dataclasses.dataclass
class Request:
    title: str
    date: Optional[datetime]
    anidb_link: str
    comment: Optional[str] = None
    remote_addr: Optional[str] = None


def get_requests() -> list[Request]:
    if not REQUESTS_PATH.exists():
        return []

    return [
        Request(
            date=dateutil.parser.parse(item["date"]) if item["date"] else None,
            title=item["title"],
            anidb_link=item["anidb_link"],
            comment=item.get("comment") or None,
            remote_addr=item.get("remote_addr") or None,
        )
        for item in jsonl.loads(REQUESTS_PATH.read_text(encoding="utf-8"))
    ]


def save_requests(requests: Iterable[Request]) -> None:
    items: list[Any] = []
    for request in requests:
        item = dataclasses.asdict(request)
        item["date"] = str(item["date"]) if item["date"] is not None else None
        items.append(item)

    REQUESTS_PATH.write_text(jsonl.dumps(items))


def is_valid_anidb_link(link: str) -> bool:
    return link.startswith("https://anidb.net/")


def get_anidb_link_id(link: str) -> Optional[int]:
    match = re.search("(\d+)", link)
    return int(match.group(1)) if match else None


def is_same_anidb_link(link1: str, link2: str) -> bool:
    link1_id = get_anidb_link_id(link1)
    link2_id = get_anidb_link_id(link2)
    return link1_id == link2_id
