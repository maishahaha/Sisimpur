from django.shortcuts import render

def home(request):
    """
    Render the home page of the dashboard.
    """
    return render(request, "dashboard.html")