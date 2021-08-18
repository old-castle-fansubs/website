from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from oc_website.models import FeaturedImage


def view_home(request: HttpRequest) -> HttpResponse:
    featured_image = (
        FeaturedImage.objects.filter(feature_date__lte=timezone.now())
        .order_by("-feature_date")
        .first()
    )
    return render(
        request, "home.html", context={"featured_image": featured_image}
    )


def view_404(request: HttpRequest, _exception: Exception) -> HttpResponse:
    return render(request, "404.html")
