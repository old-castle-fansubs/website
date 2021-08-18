from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path
from oc_website import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.view_home, name="home"),
    path("news", views.view_home, name="news"),
    path("about", views.view_about, name="about"),
    path("projects", views.view_projects, name="projects"),
    path("projects/<str:slug>", views.view_project, name="project"),
    path("guest_book", views.view_home, name="guest_book"),
    path("requests", views.view_home, name="requests"),
    path("featured_images", views.view_home, name="featured_images"),
]
urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = views.view_404
