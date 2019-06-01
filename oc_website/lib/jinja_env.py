import typing as T

import jinja2

from oc_website.lib.common import TEMPLATES_DIR


def setup_jinja_env(jinja_env: jinja2.Environment) -> None:
    jinja_env.lstrip_blocks = True
    jinja_env.trim_blocks = True
    jinja_env.add_extension("jinja2.ext.loopcontrols")
    jinja_env.add_extension("jinja2.ext.do")

    def match(haystack: str, needle: str) -> bool:
        return needle.lower() in haystack.lower()

    jinja_env.tests["match"] = match


def get_jinja_env() -> jinja2.Environment:
    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR))
    )
    setup_jinja_env(jinja_env)
    return jinja_env
