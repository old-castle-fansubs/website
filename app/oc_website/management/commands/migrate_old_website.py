import json
import re
from itertools import groupby
from pathlib import Path

import dateutil.parser
from django.core.files import File
from django.core.management.base import BaseCommand
from oc_website.management.commands._common import get_jinja_env
from oc_website.models import (
    AnimeRequest,
    Comment,
    FeaturedImage,
    Language,
    News,
    NewsAttachment,
    Project,
    ProjectExternalLink,
    ProjectRelease,
    ProjectReleaseFile,
    ProjectReleaseLink,
)
from oc_website.taxonomies import CommentContext, ProjectStatus


class Command(BaseCommand):
    help = "Migrate old website from a given directory."

    def add_arguments(self, parser):
        parser.add_argument(
            "root_dir", type=Path, help="root dir of the old website"
        )
        parser.add_argument("--news", action="store_true", help="migrate news")
        parser.add_argument(
            "--featured-images",
            action="store_true",
            help="migrate featured images",
        )
        parser.add_argument(
            "--projects",
            action="store_true",
            help="migrate projects and releases",
        )
        parser.add_argument(
            "--requests", action="store_true", help="migrate anime requests"
        )
        parser.add_argument(
            "--comments", action="store_true", help="migrate comments"
        )

    def handle(self, *_args, **options):
        root_dir = options["root_dir"]
        if options["news"]:
            self.migrate_news(root_dir)
        if options["featured_images"]:
            self.migrate_featured_images(root_dir)
        if options["projects"]:
            project_id_to_release_filter = self.migrate_projects(root_dir)
            self.migrate_project_releases(
                root_dir, project_id_to_release_filter
            )
        if options["requests"]:
            self.migrate_requests(root_dir)
        if options["comments"]:
            self.migrate_comments(root_dir)

    def migrate_news(self, root_dir: Path) -> None:
        self.stdout.write("Migrating news")
        news_dir = root_dir / "oc_website" / "templates" / "news"

        jinja_env = get_jinja_env()
        for news_file in news_dir.glob("*.html"):
            template = jinja_env.from_string(news_file.read_text())
            attachments = []
            news = News.objects.filter(slug=news_file.stem).first()
            if not news:
                news = News()

            def url_for(path: str, **kwargs: str) -> str:
                # pylint: disable=cell-var-from-loop
                full_path = f"{path}/{'/'.join(kwargs.values())}"
                if path == "static":
                    attachment = NewsAttachment(news=news)
                    local_path = root_dir / "oc_website" / full_path
                    with local_path.open("rb") as handle:
                        attachment.file.save(
                            local_path.name, File(handle), save=False
                        )
                    attachments.append(attachment)
                    return attachment.file.url
                return full_path

            context = template.new_context({"url_for": url_for})
            blocks = {
                block: "".join(func(context))
                for block, func in template.blocks.items()
            }

            news.publication_date = dateutil.parser.parse(blocks["news_date"])
            news.title = blocks["news_title"]
            news.author = blocks["news_author"]
            news.slug = news_file.stem
            news.content = re.sub(
                r"([a-z,\.])\n\s*(?!=<)",
                r"\1 ",
                blocks["news_content"].strip(),
                flags=re.M,
            )
            news.save()

            for attachment in attachments:
                attachment.save()

    def migrate_featured_images(self, root_dir: Path) -> None:
        self.stdout.write("Migrating featured images")
        FeaturedImage.objects.all().delete()

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
        Project.objects.all().delete()

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

            project, _is_created = Project.objects.update_or_create(
                title=re.sub("<[^>]*>", "", blocks["project_title"]),
                defaults=dict(
                    slug=project_file.stem,
                    status={
                        "ongoing": ProjectStatus.ACTIVE.value,
                        "finished": ProjectStatus.FINISHED.value,
                    }[blocks["project_status"]],
                    synopsis=blocks["project_synopsis"],
                    notes=blocks["project_notes"],
                    takedown_request=(
                        blocks["project_takedown_request"]
                        if "project_takedown_request" in blocks
                        else None
                    ),
                ),
            )

            if not project.small_image:
                image_path = (
                    root_dir
                    / "oc_website"
                    / "static"
                    / "img"
                    / "projects"
                    / f"{project.slug}-small.jpg"
                )
                with image_path.open("rb") as handle:
                    project.small_image.save(
                        image_path.name, File(handle), save=True
                    )

            if not project.big_image:
                image_path = (
                    root_dir
                    / "oc_website"
                    / "static"
                    / "img"
                    / "projects"
                    / f"{project.slug}-big.jpg"
                )
                with image_path.open("rb") as handle:
                    project.big_image.save(
                        image_path.name, File(handle), save=True
                    )

            for part in blocks.get("project_anidb_id", "").split(","):
                anidb_id = int(part.strip())
                ProjectExternalLink.objects.get_or_create(
                    project=project,
                    url=f"https://anidb.net/anime/{anidb_id}",
                )

            ret[project.pk] = blocks["project_release_filter"]

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
                    filename=re.sub("/.*", "", items[0]["file"]),
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

    def migrate_requests(self, root_dir: Path) -> None:
        # pylint: disable=too-many-locals,too-many-branches
        self.stdout.write("Migrating requests")

        anime_requests_path = root_dir / "data" / "requests.jsonl"
        old_anime_requests = [
            json.loads(line)
            for line in anime_requests_path.read_text().splitlines()
        ]

        to_create = []
        to_update = []

        for old_anime_request in old_anime_requests:
            anidb_url = old_anime_request["anidb_link"]
            if new_anime_request := AnimeRequest.objects.filter(
                anidb_url=anidb_url
            ).first():
                to_update.append(new_anime_request)
            else:
                new_anime_request = AnimeRequest(anidb_url=anidb_url)
                to_create.append(new_anime_request)
            new_anime_request.title = old_anime_request["title"]
            new_anime_request.request_date = (
                dateutil.parser.parse(date)
                if (date := old_anime_request.get("date"))
                else None
            )
            new_anime_request.comment = old_anime_request["comment"]
            new_anime_request.remote_addr = old_anime_request["remote_addr"]

        AnimeRequest.objects.bulk_create(to_create)
        AnimeRequest.objects.bulk_update(
            to_update, ["comment", "title", "request_date", "remote_addr"]
        )

    def migrate_comments(self, root_dir: Path) -> None:
        # pylint: disable=too-many-locals,too-many-branches
        self.stdout.write("Migrating comments")

        comments_path = root_dir / "data" / "comments.jsonl"
        old_comments = [
            json.loads(line) for line in comments_path.read_text().splitlines()
        ]

        to_create = []
        to_update = []

        for old_comment in old_comments:
            comment_id = old_comment["id"]
            if new_comment := Comment.objects.filter(pk=comment_id).first():
                to_update.append(new_comment)
            else:
                new_comment = Comment(pk=comment_id)
                to_create.append(new_comment)
            new_comment.parent_comment_id = old_comment["pid"]
            new_comment.comment_date = dateutil.parser.parse(
                old_comment["created"]
            )
            new_comment.context = (
                CommentContext.GUESTBOOK.value
                if old_comment["tid"] == 10
                else CommentContext.NEWS.value
            )
            new_comment.text = old_comment["text"]
            new_comment.remote_addr = old_comment["remote_addr"]
            new_comment.author = old_comment["author"]
            new_comment.email = old_comment["email"]
            new_comment.website = old_comment["website"]

        Comment.objects.bulk_create(to_create)
        Comment.objects.bulk_update(
            to_update,
            [
                "parent_comment_id",
                "comment_date",
                "context",
                "text",
                "remote_addr",
                "author",
                "email",
                "website",
            ],
        )
