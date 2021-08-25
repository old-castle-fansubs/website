import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional, cast

import requests
import torf
import tqdm
from celery import Celery
from celery.schedules import crontab
from django.conf import settings
from django.utils import timezone
from oc_website.celery import app
from oc_website.models import ProjectRelease, ProjectReleaseLink


class BasePublisher:
    name: str = NotImplemented

    def publish(self, torrent_path: Path, dry_run: bool) -> Optional[str]:
        raise NotImplementedError("not implemented")


class AnidexPublisher(BasePublisher):
    name = "anidex.info"

    def publish(self, torrent_path: Path, dry_run: bool) -> Optional[str]:
        with torrent_path.open("rb") as handle:
            data = {
                "api_key": settings.ANIDEX_API_KEY,
                "subcat_id": settings.ANIDEX_CATEGORY_ID,
                "lang_id": settings.ANIDEX_LANGUAGE_ID,
                "group_id": settings.ANIDEX_GROUP_ID,
                "tt_api": 1,
                "private": 0,
            }
            files = {"file": handle}

            if dry_run:
                print(
                    "publishing to anidex.info "
                    f"(payload={json.dumps(data)}, files={files})"
                )
                return None

            for _i in range(settings.ANIDEX_MAX_RETRIES):
                try:
                    response = requests.post(
                        settings.ANIDEX_API_URL, data=data, files=files
                    )
                    response.raise_for_status()
                except Exception:  # pylint: disable=broad-except
                    continue
                else:
                    break

        response.raise_for_status()
        if not response.text.startswith("https://"):
            raise ValueError(response.text)
        return response.text


class NyaaSiPublisher(BasePublisher):
    name = "nyaa.si"

    def publish(self, torrent_path: Path, dry_run: bool) -> Optional[str]:
        with torrent_path.open("rb") as handle:
            data = {
                "torrent_data": json.dumps(
                    {
                        "name": torrent_path.stem,
                        "category": settings.NYAA_SI_CATEGORY_ID,
                        "information": settings.NYAA_SI_INFO,
                        "description": "",
                        "anonymous": False,
                        "hidden": False,
                        "complete": False,
                        "remake": False,
                        "trusted": True,
                    }
                )
            }
            files = {"torrent": handle}

            if dry_run:
                print(
                    "publishing to nyaa.si "
                    f"(payload={json.dumps(data)}, files={files})"
                )
                return None

            response = requests.post(
                settings.NYAA_SI_API_URL,
                auth=(settings.NYAA_SI_USER, settings.NYAA_SI_PASS),
                data=data,
                files=files,
            )

        response.raise_for_status()
        result = response.json()
        if result.get("errors"):
            raise ValueError(result["errors"])
        return cast(str, result["url"])


class NyaaPantsuPublisher(BasePublisher):
    name = "nyaa.net"

    def publish(self, torrent_path: Path, dry_run: bool) -> Optional[str]:
        with torrent_path.open("rb") as handle:
            data = {
                "username": settings.NYAA_PANTSU_USER,
                "name": torrent_path.stem,
                "magnet": None,
                "c": settings.NYAA_PANTSU_CATEGORY_ID,
                "remake": False,
                "desc": "",
                "status": None,
                "hidden": False,
                "website_link": settings.NYAA_PANTSU_WEBSITE,
                "languages": settings.NYAA_PANTSU_LANGUAGES,
            }
            files = {"torrent": handle}
            headers = {"Authorization": settings.NYAA_PANTSU_API_KEY}

            if dry_run:
                print(
                    "publishing to nyaa.pantsu "
                    f"(payload={json.dumps(data)}, "
                    f"headers={headers}, "
                    f"files={files})"
                )
                return None

            response = requests.post(
                settings.NYAA_PANTSU_API_URL,
                headers=headers,
                data=data,
                files=files,
            )

        response.raise_for_status()
        result = response.json()
        if result.get("errors"):
            raise ValueError(result["errors"])
        torrent_id = result["data"]["id"]
        return f"https://nyaa.net/view/{torrent_id}"


def get_torrent_name(data_path: Path) -> str:
    if data_path.is_file():
        return data_path.stem + ".torrent"
    return data_path.name + ".torrent"


@contextmanager
def chdir(path: Path) -> Iterator[None]:
    old_dir = Path(os.getcwd())
    os.chdir(path)
    yield
    os.chdir(old_dir)


def build_torrent_file(data_path: Path, torrent_path: Path) -> torf.Torrent:
    torrent = torf.Torrent(
        path=data_path.relative_to(settings.DATA_DIR),
        trackers=settings.TORRENT_TRACKERS,
    )
    torrent.piece_size = min(
        torrent.piece_size, settings.TORRENT_MAX_PIECE_SIZE
    )

    with tqdm.tqdm(total=9e9) as progress_bar:

        def callback(
            _torrent: Any,
            filepath: Path,
            pieces_done: int,
            pieces_total: int,
        ) -> None:
            progress_bar.set_description(str(filepath))
            progress_bar.update(pieces_done - progress_bar.n)
            progress_bar.total = pieces_total

        torrent.generate(callback=callback)

    torrent.write(torrent_path, overwrite=True)
    return torrent


def add_or_update_release_link(
    release: ProjectRelease, url: str, search: str
) -> None:
    if link := release.links.filter(url__contains=search).first():
        link.url = url
        link.save()
    else:
        link = ProjectReleaseLink.objects.create(release=release, url=url)
    return link


@app.on_after_finalize.connect
def setup_periodic_tasks(sender: Celery, **_kwargs: Any) -> None:
    sender.add_periodic_task(crontab(), publish_due_releases.s())


@app.task
def publish_due_releases() -> None:
    for release in ProjectRelease.objects.filter(
        scheduled_publication_date__lte=timezone.now(), is_visible=False
    ).all():
        publish_release.delay(release.pk, dry_run=False)


@app.task
def publish_release_to_third_party(
    publisher_cls_name: str, release_id: int, dry_run: bool
) -> None:
    for publisher_cls in BasePublisher.__subclasses__():
        if publisher_cls.name == publisher_cls_name:
            publisher = publisher_cls()
            break
    else:
        raise RuntimeError(
            f"invalid publisher class name: {publisher_cls_name}"
        )

    release = ProjectRelease.objects.get(pk=release_id)
    if release.links.filter(url__contains=publisher.name).exists():
        return

    data_path = settings.DATA_DIR / release.filename
    torrent_path = settings.TORRENTS_DIR / get_torrent_name(data_path)

    url = publisher.publish(torrent_path, dry_run=dry_run)
    if not url:
        return
    add_or_update_release_link(release=release, url=url, search=publisher.name)


@app.task
def publish_release(release_id: int, dry_run: bool) -> None:
    release = ProjectRelease.objects.get(pk=release_id)

    if not dry_run:
        # don't let scheduler pick it up again in its next run
        release.scheduled_publication_date = None
        release.save()

    if not release.filename:
        raise RuntimeError("Release is missing a filename")

    data_path = settings.DATA_DIR / release.filename
    torrent_path = settings.TORRENTS_DIR / get_torrent_name(data_path)

    if not torrent_path.exists():
        with chdir(settings.DATA_DIR):
            torrent = build_torrent_file(data_path, torrent_path)

            add_or_update_release_link(
                release=release, url=str(torrent.magnet()), search="magnet"
            )

            (
                settings.TRANSMISSION_WATCHDIR / get_torrent_name(data_path)
            ).write_bytes(torrent_path.read_bytes())

    for publisher_cls in BasePublisher.__subclasses__():
        publish_release_to_third_party.delay(
            publisher_cls_name=publisher_cls.name,
            release_id=release_id,
            dry_run=dry_run,
        )

    if not dry_run:
        release.is_visible = True
        release.save()
