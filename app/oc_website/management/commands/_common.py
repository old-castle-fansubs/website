import datetime

import jinja2


def setup_jinja_env(jinja_env: jinja2.Environment) -> None:
    jinja_env.lstrip_blocks = True
    jinja_env.trim_blocks = True
    jinja_env.add_extension("jinja2.ext.loopcontrols")
    jinja_env.add_extension("jinja2.ext.do")
    jinja_env.globals["deployment_id"] = datetime.datetime.now().isoformat()


def get_jinja_env() -> jinja2.Environment:
    jinja_env = jinja2.Environment()
    setup_jinja_env(jinja_env)
    return jinja_env
