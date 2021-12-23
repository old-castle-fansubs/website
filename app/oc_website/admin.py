from django import forms
from django.contrib import admin
from django.db.models.aggregates import Count, Max

from oc_website.models import (
    AniDBEntry,
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


@admin.action(description="Mark selected objects as visible")
def make_visible(_modeladmin, _request, queryset):
    queryset.update(is_visible=True)


@admin.action(description="Mark selected objects as invisible")
def make_invisible(_modeladmin, _request, queryset):
    queryset.update(is_visible=False)


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
    actions = [make_visible, make_invisible]

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


class NewsAttachmentInline(admin.StackedInline):
    model = NewsAttachment


class NewsAdminForm(forms.ModelForm):
    class Meta:
        model = News
        exclude: list[str] = []
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "monospace",
                    "rows": 30,
                    "cols": 100,
                }
            )
        }


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "publication_date"]
    inlines = [NewsAttachmentInline]
    form = NewsAdminForm


@admin.register(AniDBEntry)
class AniDBEntryAdmin(admin.ModelAdmin):
    search_fields = [
        "anidb_id",
        "title",
    ]
    list_display = [
        "anidb_id",
        "episodes",
        "image",
        "title",
        "type",
    ]


@admin.register(AnimeRequest)
class AnimeRequestAdmin(admin.ModelAdmin):
    search_fields = [
        "anidb_entry__anidb_id",
        "anidb_entry__title",
    ]
    list_display = [
        "anidb_entry_anidb_id",
        "anidb_entry_title",
    ]

    def anidb_entry_anidb_id(self, instance) -> int:
        return instance.anidb_entry.anidb_id

    def anidb_entry_title(self, instance) -> str:
        return instance.anidb_entry.title


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    search_fields = ["author", "text", "website", "remote_addr"]
    list_display = [
        "content_object",
        "comment_date",
        "author",
        "remote_addr",
    ]
    list_filter = ["content_type"]
