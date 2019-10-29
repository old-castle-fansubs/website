import dataclasses
import json
import typing as T
from datetime import datetime

import dateutil.parser

from oc_website.lib.common import DATA_DIR

REQUESTS_PATH = DATA_DIR / "requests.json"


@dataclasses.dataclass
class Request:
    title: str
    date: T.Optional[datetime] = None
    anidb_link: T.Optional[str] = None
    comment: T.Optional[str] = None
    remote_addr: T.Optional[str] = None


def get_requests() -> T.Iterable[Request]:
    if not REQUESTS_PATH.exists():
        return
    for item in json.loads(REQUESTS_PATH.read_text()):
        date = item.pop("date", None)
        date = dateutil.parser.parse(date) if date is not None else None
        yield Request(date=date, **item)


def save_requests(requests: T.Iterable[Request]) -> None:
    items: T.List[T.Any] = []
    for request in requests:
        item = dataclasses.asdict(request)
        item["date"] = str(item["date"]) if item["date"] is not None else None
        items.append(item)

    REQUESTS_PATH.write_text(json.dumps(items, indent=4))
