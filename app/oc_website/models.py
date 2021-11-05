import hashlib
import re
from collections import OrderedDict
from typing import Optional

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Count, IntegerField, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from oc_website.fields import MagnetURLField
from oc_website.markdown import render_markdown
from oc_website.taxonomies import ProjectStatus


class FeaturedImage(models.Model):
    feature_date = models.DateTimeField()
    image = models.FileField(upload_to="featured_images/")

    class Meta:
        ordering = ["-feature_date"]


class Language(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self) -> str:
        return self.name


class Project(models.Model):
    title = models.CharField(max_length=200)
    slug = models.CharField(max_length=30)
    status = models.CharField(
        max_length=30, choices=ProjectStatus.get_choices()
    )
    synopsis = models.TextField()
    notes = models.TextField(null=True, blank=True)
    takedown_request = models.CharField(blank=True, null=True, max_length=100)
    is_visible = models.BooleanField(default=True)
    big_image = models.FileField(upload_to="projects/big/")
    small_image = models.FileField(upload_to="projects/small/")

    def status_repr(self) -> str:
        return {
            ProjectStatus.ACTIVE.value: "ongoing",
            ProjectStatus.FINISHED.value: "finished",
        }[self.status]

    @property
    def languages(self) -> list[str]:
        return list(
            Language.objects.filter(projectreleasefile__release__project=self)
            .distinct()
            .values_list("name", flat=True)
            .order_by("pk")
        )

    def __str__(self) -> str:
        return self.title


class ProjectExternalLink(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="links"
    )
    url = models.URLField()

    def __str__(self) -> str:
        return f"{self.url} ({self.project})"


class ProjectRelease(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="releases"
    )
    release_date = models.DateTimeField()
    scheduled_publication_date = models.DateTimeField(null=True, blank=True)
    is_visible = models.BooleanField(default=True)
    filename = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        ordering = ["-release_date"]
        unique_together = ("project_id", "release_date")

    @property
    def languages(self) -> list[str]:
        return list(
            OrderedDict.fromkeys(sum((f.languages for f in self.files), []))
        )

    @property
    def btih(self) -> Optional[str]:
        link = self.links.filter(url__contains="magnet").first()
        if link:
            match = re.search("magnet.*btih:([0-9a-f]+)", link.url, flags=re.I)
            if match:
                return match.group(1)
        return None

    def __str__(self) -> str:
        return f"{self.project} ({self.release_date})"


class ProjectReleaseLink(models.Model):
    release = models.ForeignKey(
        ProjectRelease, related_name="links", on_delete=models.CASCADE
    )
    url = MagnetURLField(max_length=1024)

    def __str__(self) -> str:
        return f"{self.url} ({self.release})"


class ProjectReleaseFile(models.Model):
    release = models.ForeignKey(
        ProjectRelease, on_delete=models.CASCADE, related_name="files"
    )
    file_name = models.CharField(max_length=256)
    file_version = models.IntegerField()
    episode_number = models.IntegerField(null=True, blank=True)
    episode_title = models.CharField(null=True, blank=True, max_length=200)
    languages = models.ManyToManyField(Language)

    class Meta:
        ordering = ["file_name"]


class News(models.Model):
    publication_date = models.DateTimeField()
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    slug = models.CharField(max_length=30)
    content = models.TextField()
    is_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ["-publication_date"]
        verbose_name_plural = "news"

    def __str__(self) -> str:
        return f"{self.title} ({self.publication_date})"


class NewsAttachment(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE)
    file = models.FileField(upload_to="news/")


class AnimeRequestManager(models.Manager):
    def with_counts(self):
        # pylint: disable=protected-access
        content_type = ContentType.objects.get(
            model=AnimeRequest._meta.model_name
        )
        return self.annotate(
            comment_count=Coalesce(
                Subquery(
                    Comment.objects.filter(
                        content_type=content_type,
                        object_id=OuterRef("id"),
                    )
                    .values("object_id")
                    .annotate(count=Count("object_id"))
                    .values("count"),
                    output_field=IntegerField(),
                ),
                Value(0),
            )
        )


class AnimeRequest(models.Model):
    objects = AnimeRequestManager()

    request_date = models.DateTimeField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    remote_addr = models.CharField(max_length=64, null=True, blank=True)

    anidb_id = models.IntegerField()
    anidb_image = models.FileField(
        upload_to="requests/", null=True, blank=True
    )
    anidb_title = models.CharField(max_length=200, null=True, blank=True)
    anidb_type = models.CharField(max_length=30, null=True, blank=True)
    anidb_episodes = models.IntegerField(null=True, blank=True)
    anidb_synopsis = models.TextField(null=True, blank=True)
    anidb_start_date = models.DateTimeField(null=True, blank=True)
    anidb_end_date = models.DateTimeField(null=True, blank=True)

    @property
    def anidb_url(self) -> Optional[str]:
        if not self.anidb_id:
            return None
        return f"https://anidb.net/anime/{self.anidb_id}"

    class Meta:
        ordering = ["-request_date"]

    def __str__(self) -> str:
        return self.anidb_title or ""


class Comment(models.Model):
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    parent_comment = models.ForeignKey(
        "Comment",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="child_comments",
    )

    comment_date = models.DateTimeField(null=True, blank=True)
    remote_addr = models.CharField(max_length=64, null=True, blank=True)
    text = models.TextField()
    author = models.CharField(max_length=32, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    website = models.URLField(null=True, blank=True)

    is_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ["-comment_date"]

    def __str__(self) -> str:
        return (
            f"comment on {self.content_object or 'guestbook'} by {self.author}"
        )

    @property
    def html(self) -> str:
        return render_markdown(self.text)

    @property
    def author_avatar_url(self) -> str:
        chksum = hashlib.md5((self.email or self.author).encode()).hexdigest()
        return f"https://www.gravatar.com/avatar/{chksum}?d=retro"
