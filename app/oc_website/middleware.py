import pytz
from django.urls import reverse
from django.utils import timezone


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(reverse("admin:index")):
            timezone.activate(pytz.timezone("Europe/Warsaw"))
        return self.get_response(request)
