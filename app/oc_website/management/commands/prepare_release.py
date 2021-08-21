import json
import re
from pathlib import Path
from subprocess import run
from typing import Any, Optional

import ass_parser
import ass_tag_parser
import iso639
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from oc_website.models import (
    Language,
    Project,
    ProjectRelease,
    ProjectReleaseFile,
)
from oc_website.urls import url_to_edit_object


def get_iso_639_2_lang_code(lang: str) -> str:
    lang = lang.lower().replace("_", "-")
    if lang in {"en", "eng", "en-us"}:
        return "eng"
    if lang in {"pl", "pol", "pl-pl"}:
        return "pol"
    if lang in {"ro", "ro-ro"}:
        return "rum"
    if lang in {"nl", "nl-nl"}:
        return "dut"
    raise ValueError(f"unknown language {lang}")


def get_subtitle_languages(source_path: Path) -> list[str]:
    out = json.loads(
        run(
            ["mkvmerge", "-i", source_path, "-F", "json"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )
    return [
        country_code
        for track in out["tracks"]
        if track["type"] == "subtitles"
        and (
            country_code := iso639.languages.get(
                bibliographic=track["properties"]["language"]
            ).alpha2
        )
    ]


def extract_subtitles(source_path: Path, language: str) -> Optional[str]:
    out = json.loads(
        run(
            ["mkvmerge", "-i", source_path, "-F", "json"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )

    track = None
    for track in out["tracks"]:
        if (
            track["type"] == "subtitles"
            and iso639.languages.get(
                bibliographic=track["properties"]["language"]
            ).alpha2
            == language
        ):
            break

    if not track:
        return None

    track_id = track["id"]

    result = run(
        [
            "mkvextract",
            "tracks",
            "-r",
            "/dev/null",
            source_path,
            f"{track_id}:/dev/stdout",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return result.stdout


def extract_text(ass_string: str) -> str:
    ret = ""
    for ass_item in ass_tag_parser.parse_ass(ass_string):
        if isinstance(ass_item, ass_tag_parser.AssText):
            ret += ass_item.text
    return ret.replace("\\N", "\n")


def get_series_title_from_file_name(file_name: str) -> str:
    result = re.match(r"\[[^\[\]]+\] (.+?)(- \d+)? \[", file_name)
    assert result
    return result.group(1)


def get_checksum_from_file_name(file_name: str) -> str:
    result = re.search(r"\[([0-9a-f]{8})\]", file_name, flags=re.I)
    assert result
    return result.group(1)


def get_version_from_file_name(file_name: str) -> int:
    result = re.search(
        r"\[[0-9a-f]{4}([0-9a-f])[0-9a-f]{3}\]", file_name, flags=re.I
    )
    assert result
    return int(result.group(1))


def get_episode_number_from_file_name(file_name: str) -> Optional[int]:
    result = re.search(r"([0-9]+) \[[0-9a-f]{8}\]", file_name, flags=re.I)
    if not result:
        return None
    return int(result.group(1))


def get_episode_title_from_ass_file(
    ass_file: ass_parser.AssFile,
) -> Optional[str]:
    titles: list[tuple[str, str]] = []

    for event in ass_file.events:
        if event.actor == "[episode title]" or (
            event.actor == "[title]" and "series" not in event.style
        ):
            clean_title = re.sub(
                r"[–—]?\s*episode\s+#?\d+\s*[–—:]?\s*",
                "",
                extract_text(event.text),
                flags=re.I,
            )
            clean_title = re.sub(r"^[-–—\s]+", "", clean_title)
            clean_title = re.sub(r"[-–—\s]+$", "", clean_title)
            clean_title = clean_title.replace("\n", " ")
            titles.append((extract_text(event.text), clean_title))

    def sort(item: tuple[str, str]) -> Any:
        sub_text, _clean_title = item
        return not re.search(r"\d|episode", sub_text, flags=re.I)

    titles.sort(key=sort)

    if titles:
        return titles[0][1]
    return None


def get_series_title_from_release_path(path: Path) -> str:
    clean_title = path.stem
    clean_title = re.sub(r"\[[^\]]+\]", "", clean_title)
    clean_title = clean_title.strip()
    clean_title = re.sub(r"- \d+$", "", clean_title)
    clean_title = clean_title.strip()
    return clean_title


def create_release(path: Path) -> ProjectRelease:
    project_title = get_series_title_from_release_path(path)
    project = Project.objects.get(title=project_title)

    release = ProjectRelease.objects.create(
        project=project,
        release_date=timezone.now(),
        is_visible=False,
        filename=str(path.relative_to(settings.DATA_DIR)),
    )

    if path.is_file():
        subpaths = [path]
    else:
        subpaths = list(sorted(path.iterdir()))

    for subpath in subpaths:
        languages = []
        for country_code in get_subtitle_languages(subpath):
            language, _is_created = Language.objects.get_or_create(
                name=country_code
            )
            languages.append(language)

        subs_text = extract_subtitles(
            subpath, language=languages[0].name if languages else None
        )
        if subs_text:
            ass_file = ass_parser.read_ass(subs_text)
            episode_title = get_episode_title_from_ass_file(ass_file)
        else:
            episode_title = None

        release_file = ProjectReleaseFile.objects.create(
            release=release,
            file_name=str(subpath.relative_to(settings.DATA_DIR)),
            file_version=get_version_from_file_name(path.name),
            episode_number=get_episode_number_from_file_name(path.name),
            episode_title=episode_title,
        )
        release_file.languages.set(languages)

    return release


class Command(BaseCommand):
    help = "Prepare a release record based on the input file."

    def add_arguments(self, parser):
        parser.add_argument(
            "path", type=Path, help="path to create a draft release for"
        )

    def handle(self, *_args, **options):
        path = settings.DATA_DIR / options["path"]
        release = create_release(path)
        edit_url = url_to_edit_object(release)
        print(f"Created {release} as {release.pk}")
        print(f"Edit it here: {edit_url}")
