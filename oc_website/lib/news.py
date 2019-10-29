import typing as T
from dataclasses import dataclass
from datetime import datetime

import dateutil.parser

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
        date = dateutil.parser.parse(
            "".join(template.blocks["news_date"](context))
        )
        title = "".join(template.blocks["news_title"](context))
        author = "".join(template.blocks["news_author"](context))

        yield News(date=date, title=title, author=author, stem=path.stem)
