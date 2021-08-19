from typing import Optional

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from oc_website.anidb import is_same_anidb_link, is_valid_anidb_link
from oc_website.models import AnimeRequest, FeaturedImage, News, Project
from oc_website.taxonomies import ProjectStatus


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
            ongoing_projects=projects.filter(status=ProjectStatus.ACTIVE.name),
            finished_projects=projects.filter(
                status=ProjectStatus.FINISHED.name
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


def view_news(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "news.html",
        context=dict(
            news_entries=News.objects.filter(
                publication_date__lte=timezone.now(), is_visible=True
            )
        ),
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
    return render(
        request,
        "requests.html",
        context=dict(
            requests=AnimeRequest.objects.filter(
                request_date__lte=timezone.now(),
            )
        ),
    )


def view_anime_request(request: HttpRequest) -> HttpResponse:
    title = request.POST.get("title", "").strip()
    anidb_url = request.POST.get("anidb_url", "").strip()
    comment = request.POST.get("comment", "").strip()

    remote_addr: Optional[str]
    if forwarded_for := request.META.get("X-Forwarded-For"):
        remote_addr = forwarded_for.split(",")[0]
    else:
        remote_addr = request.META.get("REMOTE_ADDR")

    anime_request = AnimeRequest(
        title=title,
        request_date=timezone.now(),
        anidb_url=anidb_url,
        comment=comment,
        remote_addr=remote_addr,
    )

    errors: list[str] = []

    if request.method == "POST":
        if request.POST.get("phone") or request.POST.get("message"):
            errors.append("Human verification failed.")
        if not anime_request.title:
            errors.append("Request title cannot be empty.")
        if not anime_request.anidb_url:
            errors.append("AniDB link cannot be empty.")
        elif not is_valid_anidb_link(anime_request.anidb_url):
            errors.append("The provided AniDB link appears to be invalid.")

        if any(
            is_same_anidb_link(anime_request.anidb_url, anidb_url)
            for anidb_url in AnimeRequest.objects.values_list(
                "anidb_url", flat=True
            )
        ):
            errors.append(
                "Anime with this AniDB link had been already requested."
            )

        if not errors:
            anime_request.save()
            return redirect("anime_requests")

    return render(
        request,
        "request.html",
        context=dict(
            anime_request=anime_request,
            errors=errors,
        ),
    )


def view_404(request: HttpRequest, _exception: Exception) -> HttpResponse:
    return render(request, "404.html")
