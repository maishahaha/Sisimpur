from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("frontend.urls")),
    path("auth/", include("authentication.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Add django-browser-reload URLs only in DEBUG mode
if settings.DEBUG:
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
