import random

from django import template
from django.conf import settings

register = template.Library()
DEPLOYMENT_ID = random.randint(0, 100_000)


@register.simple_tag
def query_transform(request, **kwargs):
    updated = request.GET.copy()

    for key, value in kwargs.items():
        if value is not None:
            updated[key] = value
        else:
            updated.pop(key, None)

    return updated.urlencode()


@register.simple_tag
def deployment_id() -> int:
    if settings.DEBUG:
        return random.randint(0, 100_000)
    return DEPLOYMENT_ID
