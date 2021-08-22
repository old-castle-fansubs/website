from typing import Any

from celery import Celery
from celery.schedules import crontab
from django.utils import timezone
from oc_website.celery import app
from oc_website.management.commands.publish_release import publish_release
from oc_website.models import ProjectRelease


@app.on_after_finalize.connect
def setup_periodic_tasks(sender: Celery, **_kwargs: Any) -> None:
    sender.add_periodic_task(crontab(minute=0), publish_due_releases.s())


@app.task
def publish_due_releases() -> None:
    for release in ProjectRelease.objects.filter(
        scheduled_publication_date__lte=timezone.now(), is_visible=False
    ).all():
        publish_release(release, dry_run=False)
