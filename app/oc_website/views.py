import re
from typing import Optional

from django.core.paginator import Paginator
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from oc_website.anidb import get_anidb_link_id, is_valid_anidb_link
from oc_website.models import (
    AnimeRequest,
    Comment,
    FeaturedImage,
    News,
    Project,
)
from oc_website.tasks import fill_anime_request
from oc_website.taxonomies import CommentContext, ProjectStatus

MAX_GUESTBOOK_COMMENTS_PER_PAGE = 10
MAX_ANIME_REQUESTS_PER_PAGE = 10


def get_page_number(request: HttpRequest) -> int:
    try:
        return int(request.GET.get("page", 1))
    except ValueError:
        return 1


def get_client_ip(request: HttpRequest) -> Optional[str]:
    if forwarded_for := request.META.get("X-Forwarded-For"):
        return forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")


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
    projects = Project.objects.filter(is_visible=True).order_by("title")
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
            publication_date__lte=timezone.now(), is_visible=True
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


def view_anime_requests(request: HttpRequest) -> HttpResponse:
    anime_requests = AnimeRequest.objects.filter(
        request_date__lte=timezone.now(),
    )
    if search_text := request.GET.get("search_text"):
        anime_requests = anime_requests.filter(
            anidb_title__icontains=search_text
        )
    if sort_style := request.GET.get("sort"):
        order_mapping = {
            "title": "anidb_title",
            "episodes": "anidb_episodes",
            "type": "anidb_type",
            "request_date": "request_date",
            "start_date": "anidb_start_date",
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


def view_anime_request_add(request: HttpRequest) -> HttpResponse:
    anidb_url = request.POST.get("anidb_url", "").strip()
    anidb_id = get_anidb_link_id(anidb_url)

    anime_request = AnimeRequest(
        request_date=timezone.now(),
        anidb_id=anidb_id,
        remote_addr=get_client_ip(request),
    )

    errors: list[str] = []

    if request.method == "POST":
        if request.POST.get("phone") or request.POST.get("message"):
            errors.append("Human verification failed.")
        if not anidb_url:
            errors.append("AniDB link cannot be empty.")
        elif not is_valid_anidb_link(anidb_url):
            errors.append("The provided AniDB link appears to be invalid.")

        if AnimeRequest.objects.filter(anidb_id=anidb_id).exists():
            errors.append(
                "Anime with this AniDB link had been already requested."
            )

        if not errors:
            anime_request.save()
            fill_anime_request.delay(anime_request.pk)
            return redirect("anime_requests")

    return render(
        request,
        "request_add.html",
        context=dict(
            anidb_url=anidb_url,
            errors=errors,
        ),
    )


def view_guest_book(request: HttpRequest) -> HttpResponse:
    all_comment_count = Comment.objects.filter(
        context=CommentContext.GUESTBOOK.value
    ).count()
    paginator = Paginator(
        Comment.objects.filter(
            context=CommentContext.GUESTBOOK.value, parent_comment_id=None
        ),
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


def view_add_comment(
    request: HttpRequest, context: str, pid: Optional[int] = None
) -> HttpResponse:
    is_preview = request.POST.get("submit") == "preview"
    text = request.POST.get("text", "").strip()
    author = request.POST.get("author", "").strip()
    website = request.POST.get("website", "").strip()
    email = request.POST.get("email", "").strip()

    parent_comment: Optional[Comment] = Comment.objects.filter(
        context=context, pk=pid
    ).first()
    if parent_comment:
        context = parent_comment.context
    if context == "guest_book":
        context = CommentContext.GUESTBOOK.value

    comment = Comment(
        context=context,
        parent_comment=parent_comment,
        comment_date=timezone.now(),
        remote_addr=get_client_ip(request),
        text=text,
        author=author,
        email=email,
        website=website,
    )

    errors: list[str] = []

    if request.method == "POST":
        if request.POST.get("phone") or request.POST.get("message"):
            errors.append("Human verification failed.")
        if not comment.text:
            errors.append("Comment content cannot be empty.")
        if not comment.author:
            errors.append("Comment author cannot be empty.")
        if context not in {ctx.value for ctx in CommentContext}:
            errors.append("Bad comment context.")
        if not re.search("[a-zA-Z']{3,}", comment.text):
            errors.append(
                "Add a few more letters to make your comment more interesting."
            )
        last_comment = Comment.objects.filter(context=context).first()
        if (
            last_comment
            and last_comment.text == comment.text
            and last_comment.author == comment.author
        ):
            errors.append("A comment with this exact content already exists.")

        if not errors and not is_preview:
            comment.save()
            return redirect("guest_book")

    return render(
        request,
        "comment_add.html",
        context=dict(
            parent_comment=parent_comment,
            comment=comment,
            preview=is_preview,
            errors=errors,
        ),
    )
