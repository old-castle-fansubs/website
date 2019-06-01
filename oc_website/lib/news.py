import typing as T
from dataclasses import dataclass
from datetime import datetime

import arrow

from oc_website.lib.common import TEMPLATES_DIR
from oc_website.lib.jinja_env import get_jinja_env


@dataclass
class News:
    date: datetime
    title: str
    author: str
    stem: str


def get_news() -> T.Iterable[News]:
    jinja_env = get_jinja_env()

    for path in (TEMPLATES_DIR / "news").iterdir():
        template = jinja_env.get_template(str(path.relative_to(TEMPLATES_DIR)))
        context = template.new_context()
        date = arrow.get("".join(template.blocks["date"](context)))
        title = "".join(template.blocks["title"](context))
        author = "".join(template.blocks["author"](context))

        yield News(date=date, title=title, author=author, stem=path.stem)
