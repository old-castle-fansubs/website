from typing import Optional

from oc_website.anidb import fill_anidb_entry
from oc_website.celery import app
from oc_website.models import AniDBEntry


@app.task
def fill_missing_anidb_info(anidb_id: Optional[int] = None) -> None:
    queryset = AniDBEntry.objects.filter(title__isnull=True)
    if anidb_id is not None:
        queryset = queryset.filter(anidb_id=anidb_id)
    for anidb_entry in queryset.all():
        fill_anidb_entry(anidb_entry.anidb_id)
