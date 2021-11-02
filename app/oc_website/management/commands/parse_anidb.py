from django.core.management.base import BaseCommand
from oc_website.models import AnimeRequest
from oc_website.tasks.anime_requests import fill_anime_request


class Command(BaseCommand):
    help = "Reanalyzes AniDB response for a given request."

    def add_arguments(self, parser):
        parser.add_argument(
            "id",
            type=int,
            nargs="*",
            help="request ID to refresh AniDB description of",
        )

    def handle(self, *_args, **options):
        requests = AnimeRequest.objects.all().order_by("pk")
        if request_ids := options["id"]:
            requests = requests.filter(pk__in=request_ids)

        for request in requests:
            self.stdout.write(f"Analyzing {request.pk}")
            fill_anime_request(request.pk)
