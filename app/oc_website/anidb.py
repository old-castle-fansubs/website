import re
from typing import Optional


def get_anidb_link_id(link: str) -> Optional[int]:
    match = re.search(r"(\d+)", link)
    return int(match.group(1)) if match else None
