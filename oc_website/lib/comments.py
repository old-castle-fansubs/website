import hashlib
import json
import typing as T
from dataclasses import dataclass
from datetime import datetime

import dateutil.parser

from oc_website.lib.common import DATA_DIR
from oc_website.lib.markdown import render_markdown

COMMENTS_PATH = DATA_DIR / "comments.json"


@dataclass
class Comment:
    id: int
    tid: int
    pid: T.Optional[int]
    created: datetime
    remote_addr: str
    text: str
    author: str
    email: T.Optional[str]
    website: T.Optional[str]
    likes: int

    @property
    def html(self) -> str:
        return render_markdown(self.text)

    @property
    def author_avatar_url(self) -> str:
        chksum = hashlib.md5((self.email or self.author).encode()).hexdigest()
        return f"https://www.gravatar.com/avatar/{chksum}?d=retro"


def get_comments() -> T.Iterable[Comment]:
    if not COMMENTS_PATH.exists():
        return
    for entry in sorted(
        json.loads(COMMENTS_PATH.read_text()),
        key=lambda entry: entry["created"],
        reverse=True,
    ):
        yield Comment(
            id=entry["id"],
            tid=entry["tid"],
            pid=entry["pid"],
            created=(
                dateutil.parser.pare(entry["created"])
                if entry["created"]
                else None
            ),
            remote_addr=entry["remote_addr"],
            text=entry["text"],
            author=entry["author"],
            email=entry["email"],
            website=entry["website"],
            likes=entry["likes"],
        )


def save_comments(comments: T.Iterable[Comment]) -> None:
    COMMENTS_PATH.write_text(
        json.dumps(
            [
                {
                    "id": comment.id,
                    "tid": comment.tid,
                    "pid": comment.pid,
                    "created": str(comment.created),
                    "remote_addr": comment.remote_addr,
                    "text": comment.text,
                    "author": comment.author,
                    "email": comment.email,
                    "website": comment.website,
                    "likes": comment.likes,
                }
                for comment in comments
            ],
            indent=4,
        )
    )
