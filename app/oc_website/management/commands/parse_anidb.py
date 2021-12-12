from django.core.management.base import BaseCommand

from oc_website.models import AniDBEntry
from oc_website.tasks.anidb import fill_missing_anidb_info


class Command(BaseCommand):
    help = "Reanalyzes AniDB response for a given ID."

    def add_arguments(self, parser):
        parser.add_argument(
            "id",
            type=int,
            nargs="*",
            help="AniDB ID to refresh metadata of",
        )

    def handle(self, *_args, **options):
        entries = AniDBEntry.objects.all().order_by("anidb_id")
        if anidb_ids := options["id"]:
            entries = entries.filter(pk__in=anidb_ids)

        for entry in entries:
            self.stdout.write(f"Analyzing {entry.anidb_id}")
            fill_missing_anidb_info(anidb_id=entry.anidb_id)
