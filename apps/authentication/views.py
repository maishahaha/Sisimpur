from django.shortcuts import render, redirect
from django.contrib import messages


# Create your views here.
def signupin(request):
    """
    View for the sign in / sign up page
    """
    # Check if there's a social media action
    social_action = request.GET.get("social")

    if social_action:
        if social_action == "google":
            messages.info(
                request, "Google sign-in is coming soon!", extra_tags="Google Sign-In"
            )
        elif social_action == "facebook":
            messages.warning(
                request,
                "Facebook integration is under maintenance.",
                extra_tags="Facebook",
            )
        elif social_action == "github":
            messages.success(
                request, "GitHub authentication is ready to use!", extra_tags="GitHub"
            )
        elif social_action == "linkedin":
            messages.error(
                request,
                "LinkedIn sign-in is temporarily unavailable.",
                extra_tags="LinkedIn",
            )

        # Redirect back to the sign-in page without the query parameter
        return redirect("auth:signupin")

    return render(request, "signupin.html")
