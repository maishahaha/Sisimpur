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
        # Bypass in admin or if flag is off
        if settings.COMING_SOON \
           and not request.path.startswith('/admin/') \
           and not request.path.startswith(settings.STATIC_URL):
            return render(request, '../apps/frontend/templates/index.html', status=503)
        return self.get_response(request)
