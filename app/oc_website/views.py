import functools
from collections.abc import Callable
from typing import Any, Optional

from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Count, Max, Min, Q
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from oc_website.models import (
    AnimeRequest,
    Comment,
    FeaturedImage,
    News,
    Project,
)
from oc_website.taxonomies import ProjectStatus

MAX_GUESTBOOK_COMMENTS_PER_PAGE = 10
MAX_ANIME_REQUESTS_PER_PAGE = 10


def get_page_number(request: HttpRequest) -> int:
    try:
        return int(request.GET.get("page", 1))
    except ValueError:
        return 1


def staff_only(
    view: Callable[..., HttpResponse]
) -> Callable[..., HttpResponse]:
    @functools.wraps(view)
    def wrapper(
        request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        if not request.user.is_staff:
            raise Http404
        return view(request, *args, **kwargs)

    return wrapper


def view_home(request: HttpRequest) -> HttpResponse:
    featured_image = FeaturedImage.objects.filter(
        feature_date__lte=timezone.now()
    ).first()
    return render(
        request,
        "home.html",
        context=dict(
            featured_image=featured_image,
        ),
    )


def view_projects(request: HttpRequest) -> HttpResponse:
    visible = Q(releases__is_visible=True)
    projects = (
        Project.objects.filter(is_visible=True)
        .annotate(
            episode_count=Count(
                "releases__files__episode_number", filter=visible, distinct=True
            ),
            first_release=Min("releases__release_date"),
            last_release=Max("releases__release_date"),
        )
        .order_by("title")
    )
    return render(
        request,
        "projects.html",
        context=dict(
            ongoing_projects=projects.filter(
                status=ProjectStatus.ACTIVE.value
            ),
            finished_projects=projects.filter(
                status=ProjectStatus.FINISHED.value
            ),
        ),
    )


def view_project(request: HttpRequest, slug: str) -> HttpResponse:
    try:
        project = Project.objects.get(slug=slug)
    except Project.DoesNotExist as exc:
        raise Http404("Project does not exist") from exc

    return render(
        request,
        "project.html",
        context=dict(
            project=project,
            known_providers=["magnet", "nyaa.si", "nyaa.net", "anidex.info"],
        ),
    )


def view_about(request: HttpRequest) -> HttpResponse:
    return render(request, "about.html")


def view_news(
    request: HttpRequest, news_id: Optional[int] = None
) -> HttpResponse:
    if news_id:
        news_entries = News.objects.filter(pk=news_id)
    else:
        news_entries = News.objects.filter(
            publication_date__lte=timezone.now()
        )
    return render(
        request,
        "news.html",
        context=dict(news_entries=news_entries),
    )


def view_featured_images(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "featured.html",
        context=dict(
            featured_images=FeaturedImage.objects.filter(
                feature_date__lte=timezone.now()
            )
        ),
    )


@staff_only
def view_anime_requests(request: HttpRequest) -> HttpResponse:
    anime_requests = AnimeRequest.objects.with_counts().filter(
        Q(request_date__lte=timezone.now()) | Q(request_date__isnull=True),
    )
    if search_text := request.GET.get("search_text"):
        filter_arg = (
            Q(anidb_entry__title__icontains=search_text)
            | Q(anidb_entry__type__icontains=search_text)
            | Q(anidb_entry__synopsis__icontains=search_text)
        )
        try:
            filter_arg |= Q(anidb_id=int(search_text))
        except ValueError:
            pass
        anime_requests = anime_requests.filter(filter_arg)
    if sort_style := request.GET.get("sort"):
        order_mapping = {
            "title": "anidb_entry__title",
            "episodes": "anidb_entry__episodes",
            "type": "anidb_entry__type",
            "request_date": "request_date",
            "start_date": "anidb_entry__start_date",
            "comment_count": "comment_count",
        }
        order_mapping.update(
            {f"-{key}": f"-{value}" for key, value in order_mapping.items()}
        )
        anime_requests = anime_requests.order_by(
            order_mapping.get(sort_style, "-request_date")
        )
    paginator = Paginator(anime_requests, MAX_ANIME_REQUESTS_PER_PAGE)
    return render(
        request,
        "requests.html",
        context=dict(
            search_text=search_text,
            sort_style=sort_style,
            page=paginator.page(get_page_number(request)),
        ),
    )


@staff_only
def view_anime_request(request: HttpRequest, request_id: int) -> HttpResponse:
    try:
        anime_request = AnimeRequest.objects.with_counts().get(pk=request_id)
    except AnimeRequest.DoesNotExist as exc:
        raise Http404("Anime request does not exist") from exc
    return render(
        request,
        "request.html",
        context=dict(
            anime_request=anime_request,
            comments=Comment.objects.filter(
                parent_comment_id=None,
                content_type=ContentType.objects.get(
                    model=anime_request._meta.model_name  # pylint: disable=protected-access
                ),
                object_id=anime_request.id,
            ),
        ),
    )


@staff_only
def view_guest_book(request: HttpRequest) -> HttpResponse:
    all_comment_count = Comment.objects.filter(content_type=None).count()
    paginator = Paginator(
        Comment.objects.filter(content_type=None, parent_comment_id=None),
        MAX_GUESTBOOK_COMMENTS_PER_PAGE,
    )
    return render(
        request,
        "guest_book.html",
        context=dict(
            page=paginator.page(get_page_number(request)),
            all_comment_count=all_comment_count,
        ),
    )
