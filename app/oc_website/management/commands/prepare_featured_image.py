from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from oc_website.models import FeaturedImage
from oc_website.tasks.utils import get_next_release_datetime
from oc_website.urls import url_to_edit_object


def create_featured_image(path: Path) -> None:
    image = FeaturedImage.objects.create(
        image=File(file=path.open("rb"), name=path.name),
        feature_date=get_next_release_datetime(),
    )
    return image


class Command(BaseCommand):
    help = "Prepare a release record based on the input file."

    def add_arguments(self, parser):
        parser.add_argument(
            "path", type=Path, help="path to create a featured image from"
        )

    def handle(self, *_args, **options):
        path = settings.DATA_DIR / options["path"]
        image = create_featured_image(path)
        edit_url = url_to_edit_object(image)
        print(f"Created {image} as {image.pk}")
        print(f"Edit it here: {edit_url}")
