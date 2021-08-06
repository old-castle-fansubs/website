import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional

import dateutil.parser

from oc_website.lib import jsonl
from oc_website.lib.common import DATA_DIR
from oc_website.lib.markdown import render_markdown

COMMENTS_PATH = DATA_DIR / "comments.jsonl"


@dataclass
class Comment:
    comment_id: int
    parent_comment_id: Optional[int]
    thread_id: int
    created: datetime
    remote_addr: Optional[str]
    text: str
    author: str
    email: Optional[str]
    website: Optional[str]
    likes: int

    @property
    def html(self) -> str:
        return render_markdown(self.text)

    @property
    def author_avatar_url(self) -> str:
        chksum = hashlib.md5((self.email or self.author).encode()).hexdigest()
        return f"https://www.gravatar.com/avatar/{chksum}?d=retro"


def get_comments() -> list[Comment]:
    if not COMMENTS_PATH.exists():
        return []

    comments = [
        Comment(
            comment_id=entry["id"],
            parent_comment_id=entry["pid"],
            thread_id=entry["tid"],
            created=dateutil.parser.parse(entry["created"]),
            remote_addr=entry["remote_addr"],
            text=entry["text"],
            author=entry["author"],
            email=entry["email"],
            website=entry["website"],
            likes=entry["likes"],
        )
        for entry in jsonl.loads(COMMENTS_PATH.read_text(encoding="utf-8"))
    ]
    comments.sort(key=lambda comment: comment.created, reverse=True)
    return comments


def save_comments(comments: Iterable[Comment]) -> None:
    COMMENTS_PATH.write_text(
        jsonl.dumps(
            [
                {
                    "id": comment.comment_id,
                    "pid": comment.parent_comment_id,
                    "tid": comment.thread_id,
                    "created": str(comment.created),
                    "remote_addr": comment.remote_addr,
                    "text": comment.text,
                    "author": comment.author,
                    "email": comment.email,
                    "website": comment.website,
                    "likes": comment.likes,
                }
                for comment in comments
            ]
        )
    )
