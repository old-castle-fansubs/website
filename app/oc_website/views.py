from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from oc_website.models import FeaturedImage, News, Project
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


def view_404(request: HttpRequest, _exception: Exception) -> HttpResponse:
    return render(request, "404.html")
