import typing as T
from dataclasses import dataclass

from oc_website.lib.common import TEMPLATES_DIR
from oc_website.lib.env import get_env


@dataclass
class Project:
    title: str
    stem: str
    is_finished: bool

    @property
    def url(self) -> str:
        return "project-" + self.stem + ".html"


def get_projects() -> T.Iterable[Project]:
    env = get_env()

    for path in (TEMPLATES_DIR / "projects").iterdir():
        template = env.get_template(str(path.relative_to(TEMPLATES_DIR)))
        context = template.new_context()
        title = "".join(template.blocks["title"](context))
        status = "".join(template.blocks["status"](context))

        if status not in ("finished", "ongoing"):
            raise ValueError(f'Unknown status "{status}" in project "{path}"')

        yield Project(
            title=title, stem=path.stem, is_finished=status == "finished"
        )
