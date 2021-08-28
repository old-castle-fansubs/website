from typing import Any

from celery import Celery
from celery.schedules import crontab
from oc_website.celery import app
from oc_website.tasks.releases import publish_due_releases, publish_release


@app.on_after_finalize.connect
def setup_periodic_tasks(sender: Celery, **_kwargs: Any) -> None:
    sender.add_periodic_task(crontab(), publish_due_releases.s())


__all__ = [
    "publish_due_releases",
    "publish_release",
]
