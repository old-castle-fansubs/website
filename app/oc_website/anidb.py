import re
from typing import Optional


def is_valid_anidb_link(link: str) -> bool:
    return link.startswith("https://anidb.net/")


def get_anidb_link_id(link: str) -> Optional[int]:
    match = re.search(r"(\d+)", link)
    return int(match.group(1)) if match else None


def is_same_anidb_link(link1: str, link2: str) -> bool:
    link1_id = get_anidb_link_id(link1)
    link2_id = get_anidb_link_id(link2)
    return link1_id == link2_id
