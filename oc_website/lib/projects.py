import typing as T
from dataclasses import dataclass

from oc_website.lib.common import PROJ_DIR


@dataclass
class Project:
    title: str
    content: str
    stem: str
    is_finished: bool

    @property
    def url(self) -> str:
        return "project-" + self.stem + ".html"


def get_projects() -> T.Iterable[Project]:
    projects_dir = PROJ_DIR / "templates" / "projects"
    for path in projects_dir.iterdir():
        with path.open("r", encoding="utf-8") as handle:
            title = handle.readline().strip()
            status = handle.readline().strip()
            if status not in ("finished", "ongoing"):
                raise ValueError(
                    f'Unknown status "{status}" in project "{path}"'
                )
            if handle.readline().strip():
                raise ValueError(f'Expected empty line in project "{path}"')
            content = handle.read()

        yield Project(
            title=title,
            content=content,
            stem=path.stem,
            is_finished=status == "finished",
        )
