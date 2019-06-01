import typing as T

import jinja2

from oc_website.lib.common import TEMPLATES_DIR


def get_env() -> jinja2.Environment:
    env = jinja2.Environment(
        loader=jinja2.ChoiceLoader(
            [jinja2.FileSystemLoader(str(TEMPLATES_DIR))]
        ),
        lstrip_blocks=True,
        trim_blocks=True,
        extensions=["jinja2.ext.loopcontrols", "jinja2.ext.do"],
    )

    def match(haystack: str, needle: str) -> bool:
        return needle.lower() in haystack.lower()

    env.tests["match"] = match

    return env
