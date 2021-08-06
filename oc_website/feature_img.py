import argparse
import shutil
from datetime import datetime
from pathlib import Path

from oc_website.lib import jsonl
from oc_website.lib.common import STATIC_DIR
from oc_website.lib.featured_images import FEATURED_IMAGES_PATH

IMAGES_DIR = STATIC_DIR / "img" / "featured"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    featured = jsonl.loads(FEATURED_IMAGES_PATH.read_text(encoding="utf-8"))
    today = f"{datetime.today():%Y-%m-%d %H:%M:%S}"

    source_path = args.path

    try:
        today_entry = [f for f in featured if f["date"] == today][0]
    except IndexError:
        today_entry = None

    if today_entry:
        target_path = IMAGES_DIR / today_entry["name"]
    else:
        target_path = IMAGES_DIR / "{:04d}.{}".format(
            max(int(entry["name"][0:4]) for entry in featured) + 1,
            source_path.suffix.lstrip("."),
        )
        featured.insert(0, {"date": today, "name": target_path.name})

    shutil.copy(source_path, target_path)

    FEATURED_IMAGES_PATH.write_text(jsonl.dumps(featured))


if __name__ == "__main__":
    main()
