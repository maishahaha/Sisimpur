from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import json
import os

# Allow insecure transport in development
if settings.DEBUG:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Create your views here.
def signupin(request):
    """
    View for the sign in / sign up page
    """
    # If user is already authenticated, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    # Check if there's a social media action
    social_action = request.GET.get("social")

    if social_action:
        if social_action == "google":
            return redirect('auth:google_login')
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

    # Handle login form submission
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            return redirect('dashboard:home')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "signupin.html")

def google_login(request):
    """
    Initiate Google OAuth2 login flow
    """
    try:
        # Create OAuth2 flow instance
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
                    "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_OAUTH2_REDIRECT_URI],
                }
            },
            scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
            redirect_uri=settings.GOOGLE_OAUTH2_REDIRECT_URI
        )
        
        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        # Store state in session
        request.session['state'] = state
        
        return redirect(authorization_url)
    except Exception as e:
        messages.error(request, f"Error initiating Google login: {str(e)}")
        return redirect('auth:signupin')

def google_callback(request):
    """
    Handle Google OAuth2 callback
    """
    try:
        # Create OAuth2 flow instance
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
                    "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_OAUTH2_REDIRECT_URI],
                }
            },
            scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
            state=request.session.get('state'),
            redirect_uri=settings.GOOGLE_OAUTH2_REDIRECT_URI  # Explicitly set redirect URI
        )
        
        # Fetch token
        flow.fetch_token(
            authorization_response=request.build_absolute_uri(),
        )
        
        # Get user info
        credentials = flow.credentials
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        
        # Get or create user
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        email = user_info.get('email')
        if not email:
            messages.error(request, "Could not get email from Google account.")
            return redirect('auth:signupin')
            
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Create new user
            username = email.split('@')[0]
            # Ensure username is unique
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
                
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=user_info.get('given_name', ''),
                last_name=user_info.get('family_name', '')
            )
        
        # Log the user in
        login(request, user)
        messages.success(request, f"Welcome {user.get_full_name() or user.username}!")
        return redirect('dashboard:home')
        
    except Exception as e:
        messages.error(request, f"An error occurred during Google authentication: {str(e)}")
        return redirect('auth:signupin')
