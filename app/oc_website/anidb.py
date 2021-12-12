import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree

import dateutil.parser
import requests
from django.conf import settings
from django.core.files import File

from oc_website.models import AniDBEntry


def get_anidb_link_id(link: str) -> Optional[int]:
    match = re.search(r"(\d+)", link)
    return int(match.group(1)) if match else None


def is_valid_anidb_link(link: str) -> bool:
    return (
        link.startswith("https://anidb.net/")
        and get_anidb_link_id(link) is not None
    )


def is_same_anidb_link(link1: str, link2: str) -> bool:
    link1_id = get_anidb_link_id(link1)
    link2_id = get_anidb_link_id(link2)
    return link1_id == link2_id


def fill_anidb_entry(anidb_id: int) -> Optional[AniDBEntry]:
    class XmlParser:
        def __init__(self, path: Path) -> None:
            self.doc = ElementTree.parse(str(path)).getroot()

        def get_text(self, xpath: str, required: bool = True) -> str:
            node = self.doc.find(xpath)
            if node is None:
                if required:
                    raise ValueError(f"{xpath} not found")
                return ""
            return node.text or ""

    def process_synopsis(synopsis: str) -> str:
        return synopsis.replace("http", " http")

    def process_date(text: str) -> Optional[datetime]:
        try:
            return dateutil.parser.parse(text).astimezone()
        except ValueError:
            return None

    entry_cache_path = settings.ANIDB_CACHE_DIR / f"{anidb_id}.xml"
    image_cache_path = settings.ANIDB_CACHE_DIR / f"{anidb_id}.jpg"

    if entry_cache_path.exists():
        logging.info("anidb: using cached info for %d", anidb_id)
    else:
        logging.info("anidb: fetching info for %d", anidb_id)
        response = requests.get(
            "http://api.anidb.net:9001/httpapi?request=anime"
            f"&aid={anidb_id}"
            f"&client={settings.ANIDB_CLIENT}"
            f"&clientver={settings.ANIDB_CLIENTVER}"
            "&protover=1"
        )
        response.raise_for_status()
        time.sleep(2)
        entry_cache_path.parent.mkdir(parents=True, exist_ok=True)
        entry_cache_path.write_text(response.text)

    # XXX: bad programming, but that's not our fault.
    if entry_cache_path.read_text().startswith("<error"):
        return None

    doc = XmlParser(entry_cache_path)

    anidb_entry, _created = AniDBEntry.objects.update_or_create(
        anidb_id=anidb_id,
        defaults=dict(
            title=doc.get_text(".//title"),
            type=doc.get_text(".//type"),
            episodes=int(doc.get_text(".//episodecount")),
            synopsis=(
                process_synopsis(doc.get_text("./description", required=False))
                or None
            ),
            start_date=process_date(doc.get_text(".//startdate")),
            end_date=process_date(doc.get_text(".//enddate")),
        ),
    )

    image_url = "http://cdn.anidb.net/images/main/" + doc.get_text(
        ".//picture"
    )
    if image_cache_path.exists():
        logging.info("anidb: using cached picture for %d", anidb_id)
    else:
        logging.info("anidb: fetching picture for %d", anidb_id)
        response = requests.get(image_url)
        response.raise_for_status()
        time.sleep(2)
        image_cache_path.write_bytes(response.content)

    with image_cache_path.open("rb") as handle:
        anidb_entry.image.save(image_cache_path.name, File(handle), save=True)

    return anidb_entry
