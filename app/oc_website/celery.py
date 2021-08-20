"""Celery configuration."""
import os

from celery import Celery, Task

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oc_website.settings")

app = Celery("oc_website")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self: Task) -> None:
    """A debug Celery task."""
    print(f"Request: {self.request!r}")
