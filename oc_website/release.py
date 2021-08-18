import argparse
import json
import os
import re
import shlex
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from subprocess import run
from typing import Any, Iterable, Iterator, Optional, Protocol, Union, cast

import ass_tag_parser
import iso639
import pysubs2
import requests
import torf
import tqdm

from oc_website.lib import jsonl
from oc_website.lib.releases import RELEASES_PATH


class PublishFunc(Protocol):
    def __call__(self, path: Path, dry_run: bool) -> Optional[str]:
        ...


TRACKERS = [
    "http://anidex.moe:6969/announce",
    "http://nyaa.tracker.wf:7777/announce",
    "udp://tracker.uw0.xyz:6969",
]

TARGET_HOST = "oc"
TARGET_DATA_DIR = Path("srv/torrent/data")
TARGET_TORRENT_DIR = Path("srv/torrent/torrent")
LOCAL_TORRENT_DIR = Path(tempfile.gettempdir())
MAX_TORRENT_PIECE_SIZE = 4 * 1024 * 1024

ANIDEX_API_URL = "https://anidex.info/api/"
ANIDEX_API_KEY = os.environ.get("ANIDEX_API_KEY")
ANIDEX_GROUP_ID = os.environ.get("ANIDEX_GROUP_ID")
ANIDEX_CATEGORY_ID = 1
ANIDEX_LANGUAGE_ID = 1
ANIDEX_MAX_RETRIES = 3

NYAA_SI_API_URL = "https://nyaa.si/api/upload"
NYAA_SI_USER = os.environ.get("NYAA_SI_USER")
NYAA_SI_PASS = os.environ.get("NYAA_SI_PASS")
NYAA_SI_INFO = "https://oldcastle.moe"
NYAA_SI_CATEGORY_ID = "1_2"

NYAA_PANTSU_API_URL = "https://nyaa.net/api/upload"
NYAA_PANTSU_USER = os.environ.get("NYAA_PANTSU_USER")
NYAA_PANTSU_PASS = os.environ.get("NYAA_PANTSU_PASS")
NYAA_PANTSU_API_KEY = os.environ.get("NYAA_PANTSU_API_KEY")
NYAA_PANTSU_WEBSITE = "https://oldcastle.moe"
NYAA_PANTSU_CATEGORY_ID = "3_5"
NYAA_PANTSU_LANGUAGES = "en"


@contextmanager
def log_step(text: str) -> Iterator[None]:
    print(f"--- {text} ---", file=sys.stderr)
    yield
    print("", file=sys.stderr)


def publish_anidex(torrent_path: Path, dry_run: bool) -> Optional[str]:
    with torrent_path.open("rb") as handle:
        data = {
            "api_key": ANIDEX_API_KEY,
            "subcat_id": ANIDEX_CATEGORY_ID,
            "lang_id": ANIDEX_LANGUAGE_ID,
            "group_id": ANIDEX_GROUP_ID,
            "tt_api": 1,
            "private": 0,
        }
        files = {"file": handle}

        if dry_run:
            print(data)
            print(files)
            return None

        for _i in range(ANIDEX_MAX_RETRIES):
            try:
                response = requests.post(
                    ANIDEX_API_URL, data=data, files=files
                )
                response.raise_for_status()
            except Exception:
                continue
            else:
                break

    response.raise_for_status()
    if not response.text.startswith("https://"):
        raise ValueError(response.text)
    return response.text


def publish_nyaa_si(torrent_path: Path, dry_run: bool) -> Optional[str]:
    with torrent_path.open("rb") as handle:
        data = {
            "torrent_data": json.dumps(
                {
                    "name": torrent_path.stem,
                    "category": NYAA_SI_CATEGORY_ID,
                    "information": NYAA_SI_INFO,
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
            print(data)
            print(files)
            return None

        response = requests.post(
            NYAA_SI_API_URL,
            auth=(NYAA_SI_USER, NYAA_SI_PASS),
            data=data,
            files=files,
        )

    response.raise_for_status()
    result = response.json()
    if result.get("errors"):
        raise ValueError(result["errors"])
    return cast(str, result["url"])


def publish_nyaa_pantsu(torrent_path: Path, dry_run: bool) -> Optional[str]:
    with torrent_path.open("rb") as handle:
        data = {
            "username": NYAA_PANTSU_USER,
            "name": torrent_path.stem,
            "magnet": None,
            "c": NYAA_PANTSU_CATEGORY_ID,
            "remake": False,
            "desc": "",
            "status": None,
            "hidden": False,
            "website_link": NYAA_PANTSU_WEBSITE,
            "languages": NYAA_PANTSU_LANGUAGES,
        }
        files = {"torrent": handle}
        headers = {"Authorization": NYAA_PANTSU_API_KEY}

        if dry_run:
            print(data)
            print(headers)
            print(files)
            return None

        response = requests.post(
            NYAA_PANTSU_API_URL, headers=headers, data=data, files=files
        )

    response.raise_for_status()
    result = response.json()
    if result.get("errors"):
        raise ValueError(result["errors"])
    torrent_id = result["data"]["id"]
    return f"https://nyaa.net/view/{torrent_id}"


def rsync(source: Union[Path, str], target: Union[Path, str]) -> None:
    run(
        ["rsync", "-ahsv", "--progress", source, target],
        stdout=sys.stderr.fileno(),
        check=True,
    )


def get_torrent_name(local_data_path: Path) -> str:
    if local_data_path.is_file():
        return local_data_path.stem + ".torrent"
    return local_data_path.name + ".torrent"


def target_path_exists(target_path: Path) -> bool:
    return (
        run(
            ["ssh", TARGET_HOST, "test -e " + shlex.quote(str(target_path))],
            check=False,
        ).returncode
        == 0
    )


def build_torrent_file(
    local_data_path: Path, local_torrent_path: Path
) -> torf.Torrent:
    torrent = torf.Torrent(path=local_data_path, trackers=TRACKERS)
    torrent.piece_size = min(torrent.piece_size, MAX_TORRENT_PIECE_SIZE)

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

    torrent.write(local_torrent_path, overwrite=True)
    return torrent


def submit_to_transmission(local_torrent_path: Path) -> None:
    target_torrent_path = TARGET_TORRENT_DIR / local_torrent_path.name
    rsync(local_torrent_path, f"{TARGET_HOST}:{target_torrent_path}")
    run(
        [
            "ssh",
            TARGET_HOST,
            "transmission-remote",
            "-a",
            shlex.quote(str(target_torrent_path)),
        ],
        stdout=sys.stderr.fileno(),
        check=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("-d", "--dry-run", action="store_true")
    parser.add_argument(
        "--anidex",
        dest="publish_funcs",
        action="append_const",
        const=publish_anidex,
    )
    parser.add_argument(
        "--nyaa-si",
        dest="publish_funcs",
        action="append_const",
        const=publish_nyaa_si,
    )
    parser.add_argument(
        "--nyaa-pantsu",
        dest="publish_funcs",
        action="append_const",
        const=publish_nyaa_pantsu,
    )
    parser.add_argument(
        "-a",
        "--all",
        dest="publish_funcs",
        action="store_const",
        const=[publish_nyaa_pantsu, publish_anidex, publish_nyaa_si],
    )
    args = parser.parse_args()
    if args.publish_funcs is None:
        args.publish_funcs = []
    return args


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
        iso639.languages.get(
            bibliographic=track["properties"]["language"]
        ).alpha2
        for track in out["tracks"]
        if track["type"] == "subtitles"
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
    result = re.search(r"\[([0-9a-f]{8})\]", file_name, re.I)
    assert result
    return result.group(1)


def get_version_from_file_name(file_name: str) -> int:
    result = re.search(
        r"\[[0-9a-f]{4}([0-9a-f])[0-9a-f]{3}\]", file_name, re.I
    )
    assert result
    return int(result.group(1))


def get_episode_from_file_name(file_name: str) -> Optional[str]:
    result = re.search(r"([0-9]+) \[[0-9a-f]{8}\]", file_name, re.I)
    if not result:
        return None
    return result.group(1)


def get_title_from_subs(subs: pysubs2.ssafile.SSAFile) -> Optional[str]:
    titles: list[tuple[str, str]] = []

    for sub in subs:
        if sub.name == "[title]" and "series" not in sub.style:
            clean_title = re.sub(
                r"[–—]?\s*episode\s+#?\d+\s*[–—:]?\s*",
                "",
                extract_text(sub.text),
                flags=re.I,
            )
            clean_title = re.sub(r"^[-–—\s]+", "", clean_title)
            clean_title = re.sub(r"[-–—\s]+$", "", clean_title)
            clean_title = clean_title.replace("\n", " ")
            titles.append((extract_text(sub.text), clean_title))

    def sort(item: tuple[str, str]) -> Any:
        sub_text, _clean_title = item
        return not re.search(r"\d|episode", sub_text, re.I)

    titles.sort(key=sort)

    if titles:
        return titles[0][1]
    return None


def create_release_entry(
    now: datetime, path: Path, links: list[str]
) -> dict[str, Any]:
    languages = get_subtitle_languages(path)
    subs_text = extract_subtitles(path, languages[0])
    if subs_text:
        subs = pysubs2.SSAFile.from_string(subs_text)
        title = get_title_from_subs(subs)
    else:
        title = "unknown"

    return {
        "date": f"{now:%Y-%m-%d %H:%M:%S}",
        "file": path.name,
        "version": get_version_from_file_name(path.name),
        "episode": get_episode_from_file_name(path.name),
        "languages": languages,
        "title": title or "-",
        "links": list(sorted(links)),
    }


def do_release(
    path: Path, publish_funcs: list[PublishFunc], dry_run: bool
) -> Iterable[dict[str, Any]]:
    now = datetime.today()
    with log_step("Submitting data to storage space"):
        rsync(path, f"{TARGET_HOST}:{TARGET_DATA_DIR}")

    links: list[str] = []
    with log_step("Building torrent file"):
        local_torrent_path = LOCAL_TORRENT_DIR / get_torrent_name(path)
        if not local_torrent_path.exists():
            torrent = build_torrent_file(path, local_torrent_path)
        else:
            torrent = torf.Torrent.read(local_torrent_path)
        magnet_link = str(torrent.magnet())
        links.append(magnet_link)
        print(magnet_link)

    with log_step("Submitting torrent file to transmission"):
        submit_to_transmission(local_torrent_path)

    with log_step("Publishing torrent file on torrent trackers"):
        for func in publish_funcs:
            try:
                link = func(local_torrent_path, dry_run=dry_run)
                if link:
                    links.append(link)
                    print(link)
            except Exception as ex:
                print(ex, file=sys.stderr)
                continue

    with log_step("Creating release entries"):
        sub_paths = [path] if path.is_file() else sorted(path.iterdir())
        for sub_path in sub_paths:
            print("Processing", sub_path, file=sys.stderr)
            yield create_release_entry(now, sub_path, links)


def main() -> None:
    args = parse_args()

    all_releases = jsonl.loads(RELEASES_PATH.read_text(encoding="utf-8"))

    new_releases = do_release(
        path=args.path, publish_funcs=args.publish_funcs, dry_run=args.dry_run
    )

    for release in new_releases:
        if args.dry_run:
            print(json.dumps(release, indent=4))

        file_chksum = get_checksum_from_file_name(release["file"])
        for old_release in all_releases:
            tmp_chksum = get_checksum_from_file_name(old_release["file"])
            if tmp_chksum == file_chksum and not old_release.get("hidden"):
                release["links"] = list(
                    sorted(set(old_release["links"]) | set(release["links"]))
                )
                old_release.update(release)
                break
        else:
            all_releases.append(release)

    all_releases.sort(
        key=lambda release: (
            get_series_title_from_file_name(release["file"]),
            not release.get("hidden", False),
            release["episode"] or "",
            release["version"],
        )
    )
    if not args.dry_run:
        RELEASES_PATH.write_text(jsonl.dumps(all_releases))


if __name__ == "__main__":
    main()
