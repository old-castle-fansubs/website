import datetime
import re
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

    def regex_match(pattern: str, needle: str) -> bool:
        return re.search(needle, pattern, re.I)

    jinja_env.globals["deployment_id"] = datetime.datetime.now().isoformat()
    jinja_env.tests["match"] = match
    jinja_env.tests["regex_match"] = regex_match


def get_jinja_env() -> jinja2.Environment:
    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR))
    )
    setup_jinja_env(jinja_env)
    return jinja_env
