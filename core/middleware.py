from django.conf import settings
from django.shortcuts import render
from django.utils.timezone import now
from datetime import timedelta

class ComingSoonMiddleware:
    """
    When COMING_SOON=True, all non-admin URLs render the coming_soon page.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            settings.COMING_SOON
            and not request.path.startswith("/admin/")
            and not request.path.startswith(settings.STATIC_URL)
            and not request.path.startswith("/__reload__/")
            and not request.path.startswith("/submit-and-subscribe/")
        ):
            # Fixed date – only change it when you plan to update launch
            target_date_iso = settings.COMING_SOON_TARGET_DATE
            return render(request, "coming_soon/coming_soon.html", {
                "target_date": target_date_iso
            }, status=503)

        return self.get_response(request)
