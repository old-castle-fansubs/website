import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import dateutil.parser
from flask import url_for

from oc_website.lib import jsonl
from oc_website.lib.common import DATA_DIR, STATIC_DIR

FEATURED_IMAGES_PATH = DATA_DIR / "featured.jsonl"


@dataclass
class FeaturedImage:
    date: datetime
    name: str

    @property
    def relative_path(self) -> Path:
        return Path("img/featured/") / self.name

    @property
    def absolute_path(self) -> Path:
        return STATIC_DIR / self.relative_path

    @property
    def url(self) -> str:
        return url_for("static", filename=self.relative_path)

    @property
    def relative_thumbnail_path(self) -> Path:
        stem, _suffix = os.path.splitext(self.name)
        return Path("img-thumb/featured/") / (stem.rstrip(".") + ".jpg")

    @property
    def absolute_thumbnail_path(self) -> Path:
        return STATIC_DIR / self.relative_thumbnail_path

    @property
    def thumbnail_url(self) -> str:
        return url_for("static", filename=self.relative_thumbnail_path)


def get_featured_images() -> list[FeaturedImage]:
    return [
        FeaturedImage(
            dateutil.parser.parse(item["date"]),
            item["name"],
        )
        for item in jsonl.loads(
            FEATURED_IMAGES_PATH.read_text(encoding="utf-8")
        )
    ]
