import typing as T

import jinja2

from oc_website.lib.common import PROJ_DIR


class ProjectLoader(jinja2.BaseLoader):
    source = ""

    def get_source(
        self, environment: jinja2.Environment, template: str
    ) -> T.Any:
        if template != "generated_project.html":
            raise jinja2.TemplateNotFound(template)
        return (ProjectLoader.source, None, lambda: False)


def get_env() -> jinja2.Environment:
    env = jinja2.Environment(
        loader=jinja2.ChoiceLoader(
            [ProjectLoader(), jinja2.FileSystemLoader(str(PROJ_DIR / "html"))]
        ),
        lstrip_blocks=True,
        trim_blocks=True,
        extensions=["jinja2.ext.loopcontrols", "jinja2.ext.do"],
    )

    def match(haystack: str, needle: str) -> bool:
        return needle.lower() in haystack.lower()

    env.tests["match"] = match

    return env
