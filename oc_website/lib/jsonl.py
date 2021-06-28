import json


def loads(source):
    if isinstance(source, str):
        lines = source.splitlines()
    else:
        lines = source
    return [json.loads(line) for line in lines if line]


def dumps(items):
    return "\n".join(json.dumps(item) for item in items) + "\n"
