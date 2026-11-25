from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, reverse

from oc_website import views


def url_to_edit_object(obj):
    # pylint: disable=protected-access
    return settings.HOST_SITE + reverse(
        f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change",
        args=[obj.pk],
    )


urlpatterns = [
    path("admin/", admin.site.urls),
]

# home
urlpatterns += [
    path("", views.view_home, name="home"),
]

# news
urlpatterns += [
    path("news/", views.view_news, name="news"),
    path("news/<int:news_id>/", views.view_news, name="news"),
]

# about
urlpatterns += [
    path("about/", views.view_about, name="about"),
]

# projects / releases
urlpatterns += [
    path("projects/", views.view_projects, name="projects"),
    path("project/<str:slug>/", views.view_project, name="project"),
]

# anime requests and the guest book, read-only and for staff only
urlpatterns += [
    path("anime_requests/", views.view_anime_requests, name="anime_requests"),
    path(
        "anime_request/<int:request_id>/",
        views.view_anime_request,
        name="anime_request",
    ),
    path("guest_book/", views.view_guest_book, name="guest_book"),
]

# featured images
urlpatterns += [
    path(
        "featured_images/",
        views.view_featured_images,
        name="featured_images",
    ),
]

# static files
urlpatterns += [
    *staticfiles_urlpatterns(),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]
