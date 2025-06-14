from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.frontend.views import health_check


urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", health_check, name="health_check"),  # Health check endpoint
    path("health/", health_check, name="health_check_alt"),  # Alternative health check
    path("ping/", health_check, name="ping"),  # Simple ping endpoint
    path("", include("apps.frontend.urls")),
    path("auth/", include("apps.authentication.urls")),
    path("app/", include("apps.dashboard.urls")),
    path("api/brain/", include("apps.brain.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Add django-browser-reload URLs only in DEBUG mode
if settings.DEBUG:
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
