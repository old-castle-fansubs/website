import json
import re
from itertools import groupby
from pathlib import Path

import dateutil.parser
from django.core.files import File
from django.core.management.base import BaseCommand
from oc_website.management.commands._common import get_jinja_env
from oc_website.models import (
    FeaturedImage,
    Language,
    Project,
    ProjectExternalLink,
    ProjectRelease,
    ProjectReleaseFile,
    ProjectReleaseLink,
)
from oc_website.taxonomies import ProjectStatus


class Command(BaseCommand):
    help = "Migrate projects from a given directory."

    def add_arguments(self, parser):
        parser.add_argument(
            "root_dir", type=Path, help="root dir of the old website"
        )
        parser.add_argument(
            "-c", "--clean", action="store_true", help="wipe existing records"
        )

    def handle(self, *_args, **options):
        root_dir = options["root_dir"]
        if options["clean"]:
            Project.objects.all().delete()
            FeaturedImage.objects.all().delete()
        self.migrate_featured_images(root_dir)
        project_id_to_release_filter = self.migrate_projects(root_dir)
        self.migrate_project_releases(root_dir, project_id_to_release_filter)

    def migrate_featured_images(self, root_dir: Path) -> None:
        self.stdout.write("Migrating featured images")
        featured_images_path = root_dir / "data" / "featured.jsonl"
        featured_images_dir = (
            root_dir / "oc_website" / "static" / "img" / "featured"
        )
        old_featured_images = [
            json.loads(line)
            for line in featured_images_path.read_text().splitlines()
        ]
        for old_featured_image in old_featured_images:
            feature_date = dateutil.parser.parse(old_featured_image["date"])
            image_path = featured_images_dir / old_featured_image["name"]
            featured_image = FeaturedImage.objects.filter(
                feature_date=feature_date
            ).first()
            if featured_image:
                continue
            featured_image = FeaturedImage(feature_date=feature_date)
            with image_path.open("rb") as handle:
                featured_image.image.save(
                    image_path.name, File(handle), save=True
                )
            featured_image.save()

    def migrate_projects(self, root_dir: Path) -> dict[int, str]:
        # pylint: disable=too-many-locals
        self.stdout.write("Migrating projects")
        projects_dir = root_dir / "oc_website" / "templates" / "projects"

        jinja_env = get_jinja_env()
        ret: dict[int, str] = {}
        for project_file in projects_dir.glob("**/*.html"):
            template = jinja_env.from_string(project_file.read_text())

            context = template.new_context()
            blocks = {
                block: "".join(func(context))
                for block, func in template.blocks.items()
            }

            title = re.sub("<[^>]*>", "", blocks["project_title"])
            status = blocks["project_status"]
            release_filter = blocks["project_release_filter"]
            anidb_ids = (
                [
                    int(part.strip())
                    for part in blocks["project_anidb_id"].split(",")
                ]
                if blocks.get("project_anidb_id")
                else []
            )
            takedown_request = (
                blocks["project_takedown_request"]
                if "project_takedown_request" in blocks
                else None
            )

            project, _is_created = Project.objects.update_or_create(
                title=title,
                defaults=dict(
                    slug=project_file.stem,
                    status={
                        "ongoing": ProjectStatus.ACTIVE.name,
                        "finished": ProjectStatus.FINISHED.name,
                    }[status],
                    takedown_request=takedown_request,
                ),
            )

            for anidb_id in anidb_ids:
                ProjectExternalLink.objects.get_or_create(
                    project=project,
                    url=f"https://anidb.net/anime/{anidb_id}",
                )

            ret[project.pk] = release_filter

        return ret

    def migrate_project_releases(
        self, root_dir: Path, project_id_to_release_filter: dict[int, str]
    ) -> None:
        # pylint: disable=too-many-locals,too-many-branches
        self.stdout.write("Migrating project releases")
        releases_path = root_dir / "data" / "releases.jsonl"
        old_releases = [
            json.loads(line) for line in releases_path.read_text().splitlines()
        ]

        for old_release in old_releases:
            for (
                project_id,
                release_filter,
            ) in project_id_to_release_filter.items():
                if re.search(release_filter, old_release["file"], flags=re.I):
                    old_release["project_id"] = project_id
                    break
            else:
                raise RuntimeError(
                    f'{old_release["file"]} does not belong to any project'
                )

        languages: list[str] = sum(
            (old_release["languages"] for old_release in old_releases), []
        )
        for language in languages:
            Language.objects.get_or_create(name=language)

        # create releases
        releases_to_create = []
        for item in groupby(
            old_releases, key=lambda old_release: old_release["date"]
        ):
            key, group = item
            items = list(group)

            assert (
                len(set(old_release.get("hidden") for old_release in items))
                == 1
            )
            assert (
                len(set(old_release["project_id"] for old_release in items))
                == 1
            ), list(items)

            release_date = dateutil.parser.parse(key)
            is_visible = not items[0].get("hidden", False)
            project_id = items[0]["project_id"]

            releases_to_create.append(
                ProjectRelease(
                    project_id=project_id,
                    release_date=release_date,
                    is_visible=is_visible,
                )
            )
        ProjectRelease.objects.bulk_create(releases_to_create)

        # obtain release ids
        for item in groupby(
            old_releases, key=lambda old_release: old_release["date"]
        ):
            key, group = item
            for old_release in group:
                old_release["new_release_id"] = ProjectRelease.objects.get(
                    project_id=old_release["project_id"],
                    release_date=dateutil.parser.parse(key),
                    is_visible=not old_release.get("hidden", False),
                ).pk

        # create links
        links_to_create = []
        for item in groupby(
            old_releases, key=lambda old_release: old_release["date"]
        ):
            key, group = item
            items = list(group)
            assert (
                len(set(tuple(old_release["links"]) for old_release in items))
                == 1
            )
            for url in items[0]["links"]:
                links_to_create.append(
                    ProjectReleaseLink(
                        release_id=items[0]["new_release_id"], url=url
                    )
                )
        ProjectReleaseLink.objects.bulk_create(links_to_create)

        # create files
        files_to_create = []
        for item in groupby(
            old_releases, key=lambda old_release: old_release["date"]
        ):
            key, group = item
            for old_release in group:
                files_to_create.append(
                    ProjectReleaseFile(
                        release_id=old_release["new_release_id"],
                        file_name=old_release["file"],
                        file_version=old_release["version"],
                        episode_number=old_release["episode"],
                        episode_title=old_release["title"],
                    )
                )
        ProjectReleaseFile.objects.bulk_create(files_to_create)

        # obtain file ids
        files_to_create = []
        for item in groupby(
            old_releases, key=lambda old_release: old_release["date"]
        ):
            key, group = item
            for old_release in group:
                old_release["file_id"] = ProjectReleaseFile.objects.get(
                    release_id=old_release["new_release_id"],
                    file_name=old_release["file"],
                    file_version=old_release["version"],
                    episode_number=old_release["episode"],
                    episode_title=old_release["title"],
                ).pk

        # create file languages
        language_map: dict[str, int] = {
            language.name: language.pk for language in Language.objects.all()
        }
        file_languages_to_create = []
        for old_release in old_releases:
            for language in old_release["languages"]:
                file_languages_to_create.append(
                    ProjectReleaseFile.languages.through(
                        projectreleasefile_id=old_release["file_id"],
                        language_id=language_map[language],
                    )
                )
        ProjectReleaseFile.languages.through.objects.bulk_create(
            file_languages_to_create
        )
