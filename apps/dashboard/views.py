from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages

@login_required(login_url='auth:signupin')
def home(request):
    """
    Render the home page of the dashboard.
    """
    return render(request, "dashboard.html")

def logout_view(request):
    """
    Handle user logout
    """
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('auth:signupin')

@login_required(login_url='auth:signupin')
def profile(request):
    """
    Render the user profile page
    """
    return render(request, "profile.html")

@login_required(login_url='auth:signupin')
def settings(request):
    """
    Render the settings page
    """
    return render(request, "settings.html")

@login_required(login_url='auth:signupin')
def help(request):
    """
    Render the help and support page
    """
    return render(request, "help.html")