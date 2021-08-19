import re
from collections import OrderedDict
from typing import Optional

from django.db import models
from oc_website.fields import MagnetURLField
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
            ProjectStatus.ACTIVE.name: "ongoing",
            ProjectStatus.FINISHED.name: "finished",
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
    is_visible = models.BooleanField(default=True)

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
