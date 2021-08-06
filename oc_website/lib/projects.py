import re
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Iterable, Optional

from oc_website.lib.common import TEMPLATES_DIR
from oc_website.lib.jinja_env import get_jinja_env
from oc_website.lib.releases import Release


@dataclass
class Project:
    title: str
    stem: str
    status: str
    is_finished: bool
    anidb_ids: Optional[list[int]] = None
    takedown_request: Optional[str] = None
    releases: list[Release] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)

    @property
    def url(self) -> str:
        return "project-" + self.stem + ".html"


def get_projects(releases: list[Release]) -> Iterable[Project]:
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

        project_releases = list(
            sorted(
                (
                    release
                    for release in releases
                    if not release.is_hidden
                    and any(
                        re.search(
                            release_filter, release_file.file_name, flags=re.I
                        )
                        for release_file in release.files
                    )
                ),
                key=lambda release: release.date,
                reverse=status != "finished",
            )
        )

        languages: list[str] = sum(
            (release.languages for release in project_releases), []
        )
        languages = list(OrderedDict.fromkeys(languages))

        yield Project(
            title=title,
            stem=path.stem,
            status=status,
            is_finished=status == "finished",
            anidb_ids=anidb_ids,
            takedown_request=takedown_request,
            releases=project_releases,
            languages=languages,
        )
