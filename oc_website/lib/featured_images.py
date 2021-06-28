import os
import typing as T
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import dateutil.parser

from oc_website.lib import jsonl
from oc_website.lib.common import DATA_DIR, STATIC_DIR

FEATURED_IMAGES_PATH = DATA_DIR / "featured.jsonl"


@dataclass
class FeaturedImage:
    date: datetime
    name: str

    @property
    def url(self) -> str:
        return "img/featured/" + self.name

    @property
    def thumbnail_url(self) -> str:
        stem, suffix = os.path.splitext(self.name)
        return "img-thumb/featured/" + stem.rstrip(".") + ".jpg"

    @property
    def path(self) -> Path:
        return STATIC_DIR / self.url

    @property
    def thumbnail_path(self) -> Path:
        return STATIC_DIR / self.thumbnail_url


def get_featured_images() -> T.Iterable[FeaturedImage]:
    for item in jsonl.loads(FEATURED_IMAGES_PATH.read_text(encoding="utf-8")):
        yield FeaturedImage(
            dateutil.parser.parse(item["date"]),
            item["name"],
        )
