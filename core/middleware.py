# core/middleware.py
from django.conf import settings
from django.shortcuts import render


class ComingSoonMiddleware:
    """
    When COMING_SOON=True, all non-admin URLs render the coming_soon page.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Bypass in admin, static files, browser reload, or if flag is off
        if (
            settings.COMING_SOON
            and not request.path.startswith("/admin/")
            and not request.path.startswith(settings.STATIC_URL)
            and not request.path.startswith("/__reload__/")
            and not request.path.startswith("/api/subscribe/")
        ):
            return render(request, "coming_soon/coming_soon.html", status=503)
        return self.get_response(request)
