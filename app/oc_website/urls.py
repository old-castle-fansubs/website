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
    path("about", views.view_home, name="about"),
    path("projects", views.view_projects, name="projects"),
    path("guest_book", views.view_home, name="guest_book"),
]
urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = views.view_404
