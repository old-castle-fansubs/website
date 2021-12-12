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

# anime requests
urlpatterns += [
    path("anime_requests/", views.view_anime_requests, name="anime_requests"),
    path(
        "anime_request/<int:request_id>/",
        views.view_anime_request,
        name="anime_request",
    ),
    path(
        "anime_request/<int:object_id>/comment/",
        views.view_add_comment,
        {
            "content_type": "animerequest",
            "page_title": "Anime requests",
            "page_id": "requests",
        },
        name="anime_request_comment",
    ),
    path(
        "anime_request/<int:object_id>/reply/<int:pid>",
        views.view_add_comment,
        {
            "content_type": "animerequest",
            "page_title": "Anime requests",
            "page_id": "requests",
        },
        name="anime_request_comment",
    ),
    path(
        "anime_request/add/",
        views.view_anime_request_add,
        name="anime_request_add",
    ),
]

# guest book
urlpatterns += [
    path("guest_book/", views.view_guest_book, name="guest_book"),
    path(
        "guest_book/comment/",
        views.view_add_comment,
        {
            "content_type": None,
            "object_id": None,
            "page_title": "Guest book",
            "page_id": "guest-book",
        },
        name="guest_book_comment",
    ),
    path(
        "guest_book/reply/<int:pid>",
        views.view_add_comment,
        {
            "content_type": None,
            "object_id": None,
            "page_title": "Guest book",
            "page_id": "guest-book",
        },
        name="guest_book_comment",
    ),
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
