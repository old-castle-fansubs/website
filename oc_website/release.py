import argparse
import json
import re
import typing as T
from datetime import datetime
from pathlib import Path
from subprocess import run

import pysubs2

import ass_tag_parser
from oc_website.lib.releases import RELEASES_PATH


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("link", nargs="*")
    parser.add_argument("-d", "--dry-run", action="store_true")
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


def main() -> None:
    args = parse_args()

    releases = json.loads(RELEASES_PATH.read_text())

    for path in (
        [args.path] if args.path.is_file() else sorted(args.path.iterdir())
    ):
        version = get_version_from_file_name(path.name)
        episode = get_episode_from_file_name(path.name)

        subs = pysubs2.SSAFile.from_string(extract_subtitles(path))
        title = get_title_from_subs(subs)

        release = {
            "date": f"{datetime.today():%Y-%m-%d %H:%M:%S}",
            "file": path.name,
            "version": version,
            "episode": episode,
            "title": title or "-",
            "links": args.link,
        }

        releases.append(release)
        if args.dry_run:
            print(json.dumps(release, indent=4))

    if not args.dry_run:
        RELEASES_PATH.write_text(json.dumps(releases, indent=4) + "\n")


if __name__ == "__main__":
    main()
