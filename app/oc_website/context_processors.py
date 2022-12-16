from django.conf import settings


def add_settings(_request):
    return {
        "comments_enabled": settings.COMMENTS_ENABLED,
        "requests_enabled": settings.REQUESTS_ENABLED,
    }
