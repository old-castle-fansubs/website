from django.core.management.base import BaseCommand
from django.test import override_settings
from oc_website.tasks import publish_release


class Command(BaseCommand):
    help = "Prepare a release record based on the input file."

    def add_arguments(self, parser):
        parser.add_argument(
            "release_id", type=int, help="ID of release to publish"
        )
        parser.add_argument("-d", "--dry-run", action="store_true")

    def handle(self, *_args, **options):
        release_id = options["release_id"]
        dry_run = options["dry_run"]
        with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
            publish_release(release_id, dry_run)
