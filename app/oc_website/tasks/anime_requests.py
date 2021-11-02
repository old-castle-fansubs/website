import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree

import dateutil.parser
import requests
from django.conf import settings
from django.core.files import File
from oc_website.celery import app
from oc_website.models import AnimeRequest


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


@app.task
def fill_anime_request(anime_request_id: int) -> None:
    anime_request = AnimeRequest.objects.get(pk=anime_request_id)
    anidb_id = anime_request.anidb_id

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
        return

    doc = XmlParser(entry_cache_path)

    anime_request.anidb_title = doc.get_text(".//title")
    anime_request.anidb_type = doc.get_text(".//type")
    anime_request.anidb_episodes = int(doc.get_text(".//episodecount"))
    anime_request.anidb_synopsis = (
        process_synopsis(doc.get_text("./description", required=False)) or None
    )
    anime_request.anidb_start_date = process_date(doc.get_text(".//startdate"))
    anime_request.anidb_end_date = process_date(doc.get_text(".//enddate"))
    anime_request.save()

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
        anime_request.anidb_image.save(
            image_cache_path.name, File(handle), save=True
        )


@app.task
def fill_anime_requests() -> None:
    for anime_request in AnimeRequest.objects.filter(
        anidb_title__isnull=True
    ).all():
        fill_anime_request.delay(anime_request.pk)
