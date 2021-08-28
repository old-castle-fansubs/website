from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, reverse
from oc_website import views


def url_to_edit_object(obj):
    # pylint: disable=protected-access
    return reverse(
        f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change",
        args=[obj.pk],
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.view_home, name="home"),
    path("news/", views.view_news, name="news"),
    path("news/<int:news_id>/", views.view_news, name="news"),
    path("about/", views.view_about, name="about"),
    path("projects/", views.view_projects, name="projects"),
    path("project/<str:slug>/", views.view_project, name="project"),
    path("anime_requests/", views.view_anime_requests, name="anime_requests"),
    path(
        "anime_requests/add/",
        views.view_anime_request_add,
        name="anime_request_add",
    ),
    path("guest_book/", views.view_guest_book, name="guest_book"),
    path("<str:context>/add/", views.view_add_comment, name="comment_add"),
    path(
        "<str:context>/add/<int:pid>/",
        views.view_add_comment,
        name="comment_add",
    ),
    path(
        "featured_images/", views.view_featured_images, name="featured_images"
    ),
    *staticfiles_urlpatterns(),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]
