import typing as T
from dataclasses import dataclass

from oc_website.lib.common import TEMPLATES_DIR
from oc_website.lib.jinja_env import get_jinja_env


@dataclass
class Project:
    title: str
    stem: str
    release_filter: str
    status: str
    is_finished: bool
    anidb_ids: T.Optional[T.List[int]] = None
    takedown_request: T.Optional[str] = None

    @property
    def url(self) -> str:
        return "project-" + self.stem + ".html"


def get_projects() -> T.Iterable[Project]:
    jinja_env = get_jinja_env()

    for path in (TEMPLATES_DIR / "projects").iterdir():
        template = jinja_env.get_template(str(path.relative_to(TEMPLATES_DIR)))
        context = template.new_context()
        blocks = {
            block: "".join(func(context))
            for block, func in template.blocks.items()
        }

        title = blocks["project_title"]
        status = blocks["project_status"]
        release_filter = blocks["project_release_filter"]
        anidb_ids = (
            [
                int(part.strip())
                for part in blocks["project_anidb_id"].split(",")
            ]
            if blocks.get("project_anidb_id")
            else None
        )
        takedown_request = (
            blocks["project_takedown_request"]
            if "project_takedown_request" in blocks
            else None
        )

        if status not in ("finished", "ongoing"):
            raise ValueError(f'Unknown status "{status}" in project "{path}"')

        yield Project(
            title=title,
            stem=path.stem,
            status=status,
            is_finished=status == "finished",
            release_filter=release_filter,
            anidb_ids=anidb_ids,
            takedown_request=takedown_request,
        )
