from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from oc_website.models import FeaturedImage, Project
from oc_website.taxonomies import ProjectStatus


def view_home(request: HttpRequest) -> HttpResponse:
    featured_image = (
        FeaturedImage.objects.filter(feature_date__lte=timezone.now())
        .order_by("-feature_date")
        .first()
    )
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


def view_404(request: HttpRequest, _exception: Exception) -> HttpResponse:
    return render(request, "404.html")
