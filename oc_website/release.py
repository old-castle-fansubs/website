import argparse
import json
import os
import re
import shlex
import sys
import tempfile
import typing as T
from datetime import datetime
from pathlib import Path
from subprocess import run

import humanfriendly
import pysubs2
import requests
import torf
import tqdm

import ass_tag_parser
from oc_website.lib.releases import RELEASES_PATH

TRACKERS = [
    "http://anidex.moe:6969/announce",
    "http://nyaa.tracker.wf:7777/announce",
]

TARGET_HOST = "oldcastle.moe"
TARGET_DATA_DIR = Path("srv/torrent/data")
TARGET_TORRENT_DIR = Path("srv/torrent/torrent")
LOCAL_TORRENT_DIR = Path(tempfile.gettempdir())
MAX_TORRENT_PIECE_SIZE = 4 * 1024 * 1024

ANIDEX_API_URL = "https://anidex.info/api/"
ANIDEX_API_KEY = os.environ.get("ANIDEX_API_KEY")
ANIDEX_GROUP_ID = os.environ.get("ANIDEX_GROUP_ID")
ANIDEX_CATEGORY_ID = 1
ANIDEX_LANGUAGE_ID = 1

NYAA_SI_API_URL = "https://nyaa.si/api/upload"
NYAA_SI_USER = os.environ.get("NYAA_SI_USER")
NYAA_SI_PASS = os.environ.get("NYAA_SI_PASS")
NYAA_SI_INFO = "https://oldcastle.moe"
NYAA_SI_CATEGORY_ID = "1_2"


def publish_anidex(torrent_path: Path, dry_run: bool) -> None:
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
            return

        response = requests.post(ANIDEX_API_URL, data=data, files=files)

    response.raise_for_status()
    if not response.text.startswith("https://"):
        raise ValueError(response.text)
    return response.text


def publish_nyaa_si(torrent_path: Path, dry_run: bool) -> None:
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
            return
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
    return result["url"]


def rsync(source: T.Union[Path, str], target: T.Union[Path, str]) -> None:
    run(
        ["rsync", "-ahsv", "--progress", source, target],
        stdout=sys.stderr.fileno(),
        check=True,
    )


def get_torrent_name(local_data_path: Path) -> Path:
    if local_data_path.is_file():
        return local_data_path.stem + ".torrent"
    return local_data_path.name + ".torrent"


def target_path_exists(target_path: Path) -> bool:
    return (
        run(
            ["ssh", TARGET_HOST, "test -e " + shlex.quote(str(target_path))]
        ).returncode
        == 0
    )


def build_torrent_file(
    local_data_path: Path, local_torrent_path: Path
) -> None:
    print("Building torrent file", file=sys.stderr)
    torrent = torf.Torrent(path=local_data_path, trackers=TRACKERS)
    if torrent.piece_size > MAX_TORRENT_PIECE_SIZE:
        torrent.piece_size = MAX_TORRENT_PIECE_SIZE
    print(
        "Piece size:",
        humanfriendly.format_size(torrent.piece_size, binary=True),
        file=sys.stderr,
    )

    with tqdm.tqdm(total=9e9) as bar:

        def callback(_torrent, filepath, pieces_done, pieces_total):
            bar.set_description(filepath)
            bar.update(pieces_done - bar.n)
            bar.total = pieces_total

        torrent.generate(callback)

    torrent.write(local_torrent_path, overwrite=True)


def submit_to_transmission(target_torrent_path: Path) -> None:
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
    parser.add_argument("--anidex", dest="publish_anidex", action="store_true")
    parser.add_argument(
        "--nyaa-si", dest="publish_nyaa_si", action="store_true"
    )
    return parser.parse_args()


def extract_subtitles(source_path: Path) -> str:
    out = run(
        ["mkvmerge", "-i", source_path], capture_output=True, text=True
    ).stdout

    results = re.search(r"Track ID (\d+): subtitles \(SubStationAlpha\)", out)
    if not results:
        raise RuntimeError("No subtiles found in the file")
    track_id = int(results.group(1))

    return run(
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
    ).stdout


def extract_text(ass_string: str) -> str:
    ret = ""
    for ass_item in ass_tag_parser.parse_ass(ass_string):
        if isinstance(ass_item, ass_tag_parser.AssText):
            ret += ass_item.text
    return ret.replace("\\N", "\n")


def get_checksum_from_file_name(file_name: str) -> int:
    result = re.search(r"\[([0-9a-f]{8})\]", file_name, re.I)
    assert result
    return result.group(1)


def get_version_from_file_name(file_name: str) -> int:
    result = re.search(
        r"\[[0-9a-f]{4}([0-9a-f])[0-9a-f]{3}\]", file_name, re.I
    )
    assert result
    return int(result.group(1))


def get_episode_from_file_name(file_name: str) -> T.Optional[str]:
    result = re.search(r"([0-9]+) \[[0-9a-f]{8}\]", file_name, re.I)
    if not result:
        return None
    return result.group(1)


def get_title_from_subs(subs: pysubs2.ssafile.SSAFile) -> T.Optional[str]:
    titles: T.List[T.Tuple[str, str]] = []

    for sub in subs:
        if sub.name == "[title]":
            clean_title = re.sub(
                r"[–—]?\s*episode\s+#?\d+\s*[–—:]?\s*",
                "",
                extract_text(sub.text),
                flags=re.I,
            )
            titles.append((extract_text(sub.text), clean_title))

    def sort(item: T.Tuple[str, str]) -> T.Any:
        sub_text, clean_title = item
        return not re.search(r"\d|episode", sub_text, re.I)

    titles.sort(key=sort)

    if titles:
        return titles[0][1]
    return None


def do_release(path: Path, args: argparse.Namespace) -> None:
    subs = pysubs2.SSAFile.from_string(extract_subtitles(path))
    title = get_title_from_subs(subs)

    rsync(path, f"{TARGET_HOST}:{TARGET_DATA_DIR}")

    local_torrent_path = LOCAL_TORRENT_DIR / get_torrent_name(path)
    target_torrent_path = TARGET_TORRENT_DIR / get_torrent_name(path)

    if not local_torrent_path.exists():
        if target_path_exists(target_torrent_path):
            rsync(f"{TARGET_HOST}:{target_torrent_path}", local_torrent_path)
        else:
            build_torrent_file(args.path, local_torrent_path)

    if not target_path_exists(target_torrent_path):
        rsync(local_torrent_path, f"{TARGET_HOST}:{target_torrent_path}")

    submit_to_transmission(target_torrent_path)

    links: T.List[str] = []

    if args.publish_anidex:
        link = publish_anidex(local_torrent_path, args.dry_run)
        if link:
            links.append(link)

    if args.publish_nyaa_si:
        link = publish_nyaa_si(local_torrent_path, args.dry_run)
        if link:
            links.append(link)

    return {
        "date": f"{datetime.today():%Y-%m-%d %H:%M:%S}",
        "file": path.name,
        "version": get_version_from_file_name(path.name),
        "episode": get_episode_from_file_name(path.name),
        "title": title or "-",
        "links": links,
    }


def main() -> None:
    args = parse_args()

    releases = json.loads(RELEASES_PATH.read_text())

    for path in (
        [args.path] if args.path.is_file() else sorted(args.path.iterdir())
    ):
        release = do_release(path, args)

        if args.dry_run:
            print(json.dumps(release, indent=4))

        file_chksum = get_checksum_from_file_name(release["file"])
        for i, item in enumerate(releases):
            tmp_chksum = get_checksum_from_file_name(item["file"])
            if tmp_chksum == file_chksum:
                releases[i]["links"] = list(
                    set(releases[i]["links"]) | set(release["links"])
                )
                break
        else:
            releases.append(release)

    if not args.dry_run:
        RELEASES_PATH.write_text(json.dumps(releases, indent=4) + "\n")


if __name__ == "__main__":
    main()
