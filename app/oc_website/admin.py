from django.contrib import admin
from django.db.models.aggregates import Count, Max
from oc_website.models import (
    FeaturedImage,
    Language,
    Project,
    ProjectExternalLink,
    ProjectRelease,
    ProjectReleaseFile,
    ProjectReleaseLink,
)


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    pass


@admin.register(FeaturedImage)
class FeaturedImageAdmin(admin.ModelAdmin):
    pass


class ProjectExternalLinkInline(admin.StackedInline):
    model = ProjectExternalLink


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    inlines = [
        ProjectExternalLinkInline,
    ]
    list_display = ["title", "slug", "status", "is_visible"]
    ordering = ["-is_visible", "status", "title"]


class ProjectReleaseFileInline(admin.TabularInline):
    model = ProjectReleaseFile
    extra = 0


class ProjectReleaseLinkInline(admin.TabularInline):
    model = ProjectReleaseLink
    extra = 0


@admin.register(ProjectRelease)
class ProjectReleaseAdmin(admin.ModelAdmin):
    inlines = [
        ProjectReleaseFileInline,
        ProjectReleaseLinkInline,
    ]
    search_fields = ["project__title", "files__episode_number"]
    list_display = [
        "project__title",
        "release_date",
        "is_visible",
        "is_batch",
        "episode_number",
    ]
    list_filter = ["project"]
    ordering = ["-release_date"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related("project")
        queryset = queryset.annotate(
            file_count=Count("files"),
            highest_episode_number=Max("files__episode_number"),
        )
        return queryset

    def project__title(self, obj):
        return obj.project.title

    def is_batch(self, obj):
        return obj.file_count > 1

    def episode_number(self, obj):
        return obj.highest_episode_number if obj.file_count == 1 else None
