from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
import re
import json
from apps.utils import (
    send_webhook,
    send_user_signup_webhook,
    send_user_login_webhook,
    send_normal_signin_webhook,
    send_google_signin_webhook
)

# Get the User model
User = get_user_model()

# Allow insecure transport in development
if settings.DEBUG:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

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

    # Handle form submissions
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'login':
            return handle_login(request)
        elif action == 'signup':
            return handle_signup(request)

    return render(request, "signupin.html")


def handle_login(request):
    """Handle user login"""
    print(f"DEBUG: handle_login called")
    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')

    print(f"DEBUG: Login attempt - email={email}, password_provided={bool(password)}")

    # Validate input
    if not email or not password:
        print(f"DEBUG: Login validation failed - missing email or password")
        messages.error(request, "Please enter both email and password.")
        return render(request, "signupin.html")

    # Validate Gmail requirement
    if not (email.endswith('@gmail.com') or email.endswith('@googlemail.com')):
        messages.error(request, "Only Gmail addresses (@gmail.com or @googlemail.com) are allowed.")
        return render(request, "signupin.html")

    # Find user by email and authenticate
    try:
        user_obj = User.objects.get(email=email)
        print(f"DEBUG: Found user object - username={user_obj.username}, is_active={user_obj.is_active}")
        user = authenticate(request, username=user_obj.username, password=password)
        print(f"DEBUG: Authentication result - user={user}")
    except User.DoesNotExist:
        print(f"DEBUG: User not found for email={email}")
        user = None

    if user is not None:
        if user.is_active:
            print(f"DEBUG: User is active, logging in")
            login(request, user)

            # Send Discord webhook notification for normal sign in
            try:
                send_normal_signin_webhook(user)
            except Exception as e:
                print(f"DEBUG: Webhook error: {e}")

            messages.success(request, f"Welcome back, {user.get_full_name() or user.email}!")

            # Redirect to next page if specified, otherwise dashboard
            next_page = request.GET.get('next', 'dashboard:home')
            print(f"DEBUG: Redirecting to {next_page}")
            return redirect(next_page)
        else:
            print(f"DEBUG: User account is disabled")
            messages.error(request, "Your account has been disabled.")
            return render(request, "signupin.html")
    else:
        print(f"DEBUG: Authentication failed - invalid credentials")
        messages.error(request, "Invalid email or password.")
        return render(request, "signupin.html")

def handle_signup(request):
    """Handle user registration - final step after OTP verification"""
    print(f"DEBUG: handle_signup called")

    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')
    password_confirm = request.POST.get('password_confirm', '')
    email_verified = request.POST.get('email_verified', 'false')

    print(f"DEBUG: email={email}, email_verified={email_verified}")
    print(f"DEBUG: session data - pending_user_id={request.session.get('pending_user_id')}, pending_email={request.session.get('pending_email')}")

    # Check if email is verified
    if email_verified != 'true':
        print(f"DEBUG: Email not verified, email_verified={email_verified}")
        messages.error(request, "Please verify your email first.")
        return render(request, "signupin.html")

    # Get the pending user from session
    pending_user_id = request.session.get('pending_user_id')
    pending_email = request.session.get('pending_email')

    print(f"DEBUG: Retrieved from session - pending_user_id={pending_user_id}, pending_email={pending_email}")

    if not pending_user_id or pending_email != email:
        print(f"DEBUG: Session validation failed - pending_user_id={pending_user_id}, pending_email={pending_email}, form_email={email}")
        messages.error(request, "Invalid verification session. Please start over.")
        return render(request, "signupin.html")

    # Validate input
    errors = []

    if not email:
        errors.append("Email is required.")
    elif not (email.endswith('@gmail.com') or email.endswith('@googlemail.com')):
        errors.append("Only Gmail addresses (@gmail.com or @googlemail.com) are allowed.")

    if not password:
        errors.append("Password is required.")
    elif password != password_confirm:
        errors.append("Passwords do not match.")

    # Validate password strength
    if password:
        try:
            validate_password(password)
        except ValidationError as e:
            errors.extend(e.messages)

    # If there are errors, show them and return
    if errors:
        for error in errors:
            messages.error(request, error)
        return render(request, "signupin.html")

    # Update the user with the final password and activate
    try:
        print(f"DEBUG: Looking for user with id={pending_user_id}, email={email}, is_active=True")
        user = User.objects.get(id=pending_user_id, email=email, is_active=True)
        print(f"DEBUG: Found user: {user.username}, setting password")
        user.set_password(password)
        user.save()
        print(f"DEBUG: Password set and user saved")

        # Clear session data
        request.session.pop('pending_user_id', None)
        request.session.pop('pending_email', None)

        # Send welcome email
        from .email_service import EmailService
        EmailService.send_welcome_email(user, email)

        # Log the user in
        login(request, user)

        # Send Discord webhook notification
        try:
            print(f"DEBUG: Sending Discord webhook for user signup")
            webhook_result = send_user_signup_webhook(user)
            print(f"DEBUG: Webhook result: {webhook_result}")
        except Exception as webhook_error:
            print(f"DEBUG: Webhook error: {str(webhook_error)}")
            # Don't let webhook errors break the signup process
        messages.success(request, f"Welcome to Sisimpur, {user.email}! Your account has been created successfully.")
        return redirect('dashboard:home')

    except User.DoesNotExist:
        messages.error(request, "Invalid verification session. Please start over.")
        return render(request, "signupin.html")
    except Exception as e:
        messages.error(request, f"An error occurred while creating your account: {str(e)}")
        return render(request, "signupin.html")

@login_required
def logout_view(request):
    """Handle user logout"""
    username = request.user.username
    logout(request)
    messages.success(request, f"Goodbye {username}! You have been logged out successfully.")
    return redirect('home')

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

        print(f"DEBUG: Google user info received: {user_info}")

        # Get or create user
        email = user_info.get('email')
        if not email:
            messages.error(request, "Could not get email from Google account.")
            return redirect('auth:signupin')

        # Extract user information
        first_name = user_info.get('given_name', '')
        last_name = user_info.get('family_name', '')
        picture_url = user_info.get('picture', '')

        print(f"DEBUG: User details - email: {email}, name: {first_name} {last_name}, picture: {picture_url}")

        try:
            user = User.objects.get(email=email)
            print(f"DEBUG: Existing user found: {user.username}")

            # Update user info if changed
            updated = False
            if first_name and user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if last_name and user.last_name != last_name:
                user.last_name = last_name
                updated = True
            if updated:
                user.save()
                print(f"DEBUG: Updated existing user info")

        except User.DoesNotExist:
            print(f"DEBUG: Creating new user for email: {email}")
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
                first_name=first_name,
                last_name=last_name
            )
            print(f"DEBUG: Created new user: {user.username}")

        # Handle profile picture
        if picture_url:
            print(f"DEBUG: Processing profile picture: {picture_url}")
            from .utils import download_google_profile_picture, ensure_media_directories
            try:
                # Ensure media directories exist
                ensure_media_directories()

                # Download and save profile picture
                success = download_google_profile_picture(user, picture_url)
                print(f"DEBUG: Profile picture download result: {success}")

                if success:
                    print(f"DEBUG: Profile picture saved successfully for {user.username}")
                else:
                    print(f"DEBUG: Profile picture download failed, but Google URL saved as fallback")

            except Exception as e:
                print(f"DEBUG: Error downloading profile picture: {e}")
                # Still save the Google URL as fallback
                try:
                    if hasattr(user, 'profile'):
                        user.profile.google_picture_url = picture_url
                        user.profile.save()
                        print(f"DEBUG: Saved Google picture URL as fallback")
                except Exception as fallback_error:
                    print(f"DEBUG: Failed to save Google URL fallback: {fallback_error}")
        else:
            print(f"DEBUG: No profile picture URL provided")
        
        # Log the user in
        login(request, user)

        # Send Discord webhook notification
        send_google_signin_webhook(user)
        messages.success(request, f"Welcome {user.get_full_name() or user.username}!")
        return redirect('dashboard:home')
        
    except Exception as e:
        messages.error(request, f"An error occurred during Google authentication: {str(e)}")
        return redirect('auth:signupin')

def verify_otp(request):
    """Handle OTP verification"""
    # Check if user has pending verification
    pending_user_id = request.session.get('pending_user_id')
    pending_email = request.session.get('pending_email')

    if not pending_user_id or not pending_email:
        messages.error(request, "No pending verification found. Please sign up again.")
        return redirect('auth:signupin')

    try:
        user = User.objects.get(id=pending_user_id, email=pending_email, is_active=False)
    except User.DoesNotExist:
        messages.error(request, "Invalid verification session. Please sign up again.")
        return redirect('auth:signupin')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'verify':
            return handle_otp_verification(request, user, pending_email)
        elif action == 'resend':
            return handle_otp_resend(request, user, pending_email)

    context = {
        'email': pending_email,
        'username': user.username,
    }
    return render(request, "verify_otp.html", context)

def handle_otp_verification(request, user, email):
    """Handle OTP verification submission"""
    otp_code = request.POST.get('otp_code', '').strip()

    if not otp_code:
        messages.error(request, "Please enter the verification code.")
        return render(request, "verify_otp.html", {'email': email, 'username': user.username})

    # Get the latest OTP for this user/email
    from .models import EmailOTP
    try:
        otp = EmailOTP.objects.filter(
            user=user,
            email=email,
            is_verified=False
        ).latest('created_at')

        if otp.verify(otp_code):
            # OTP verified successfully
            user.is_active = True
            user.save()

            # Clear session data
            request.session.pop('pending_user_id', None)
            request.session.pop('pending_email', None)

            # Send welcome email
            from .email_service import EmailService
            EmailService.send_welcome_email(user, email)

            # Log the user in
            login(request, user)
            messages.success(request, f"Email verified successfully! Welcome to Sisimpur, {user.username}!")
            return redirect('dashboard:home')
        else:
            if otp.is_expired():
                messages.error(request, "Verification code has expired. Please request a new one.")
            elif otp.attempts >= 3:
                messages.error(request, "Too many failed attempts. Please request a new verification code.")
            else:
                remaining_attempts = 3 - otp.attempts
                messages.error(request, f"Invalid verification code. {remaining_attempts} attempts remaining.")

    except EmailOTP.DoesNotExist:
        messages.error(request, "No verification code found. Please request a new one.")

    context = {
        'email': email,
        'username': user.username,
    }
    return render(request, "verify_otp.html", context)

def handle_otp_resend(request, user, email):
    """Handle OTP resend request"""
    from .models import EmailOTP
    from .email_service import EmailService
    from django.utils import timezone

    # Check if user can request a new OTP (cooldown period)
    cooldown_minutes = settings.OTP_CONFIG.get('RESEND_COOLDOWN_MINUTES', 2)
    recent_otp = EmailOTP.objects.filter(
        user=user,
        email=email,
        created_at__gte=timezone.now() - timezone.timedelta(minutes=cooldown_minutes)
    ).first()

    if recent_otp:
        messages.warning(request, f"Please wait {cooldown_minutes} minutes before requesting a new code.")
        context = {
            'email': email,
            'username': user.username,
        }
        return render(request, "verify_otp.html", context)

    # Generate and send new OTP
    try:
        otp = EmailOTP.generate_otp(user, email)
        email_sent = EmailService.send_otp_email(user, email, otp.otp_code)

        if email_sent:
            messages.success(request, f"New verification code sent to {email}")
        else:
            messages.error(request, "Failed to send verification code. Please try again.")
    except Exception as e:
        messages.error(request, f"Error sending verification code: {str(e)}")

    context = {
        'email': email,
        'username': user.username,
    }
    return render(request, "verify_otp.html", context)

@csrf_exempt
def send_otp_ajax(request):
    """AJAX endpoint to send OTP"""
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"OTP AJAX request received - Method: {request.method}")

    if request.method != 'POST':
        logger.warning("Invalid method for OTP request")
        return JsonResponse({'success': False, 'message': 'Method not allowed'})

    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()

        logger.info(f"OTP request for email: {email}")

        # Get client IP address
        def get_client_ip(request):
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            return ip

        client_ip = get_client_ip(request)
        logger.info(f"Request from IP: {client_ip}")

        # Validate email
        if not email or not (email.endswith('@gmail.com') or email.endswith('@googlemail.com')):
            logger.warning(f"Invalid email format: {email}")
            return JsonResponse({'success': False, 'message': 'Only Gmail addresses (@gmail.com or @googlemail.com) are allowed'})

        # Check rate limiting
        from .models import OTPRateLimit
        rate_limit_ok, rate_limit_message = OTPRateLimit.check_rate_limit(email, client_ip)
        if not rate_limit_ok:
            logger.warning(f"Rate limit exceeded for {email} from {client_ip}")
            return JsonResponse({'success': False, 'message': rate_limit_message})

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            logger.warning(f"Email already exists: {email}")
            return JsonResponse({'success': False, 'message': 'Email already registered. Please try logging in.'})

        # Create temporary user for OTP
        username = email.split('@')[0]
        original_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1

        logger.info(f"Creating user with username: {username}")

        # Create inactive user
        user = User.objects.create_user(
            username=username,
            email=email,
            password='temp_password',  # Will be updated after OTP verification
            is_active=False
        )

        logger.info(f"User created successfully: {user.id}")

        # Generate and send OTP
        from .models import EmailOTP
        from .email_service import EmailService

        otp = EmailOTP.generate_otp(user, email, client_ip)
        logger.info(f"OTP generated and hashed securely")

        # Use the temporary plain OTP for email sending
        email_sent = EmailService.send_otp_email(user, email, otp._plain_otp)
        logger.info(f"Email sent result: {email_sent}")

        if email_sent:
            # Store user ID in session
            request.session['pending_user_id'] = user.id
            request.session['pending_email'] = email
            logger.info(f"Session data stored for user: {user.id}")
            return JsonResponse({'success': True, 'message': 'Verification code sent successfully'})
        else:
            logger.error("Failed to send email, deleting user")
            user.delete()
            return JsonResponse({'success': False, 'message': 'Failed to send verification code'})

    except Exception as e:
        logger.error(f"Exception in send_otp_ajax: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})

@csrf_exempt
def verify_otp_ajax(request):
    """AJAX endpoint to verify OTP"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'})

    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        otp_code = data.get('otp_code', '').strip()

        # Get pending user from session
        pending_user_id = request.session.get('pending_user_id')
        if not pending_user_id:
            return JsonResponse({'success': False, 'message': 'No pending verification found'})

        try:
            user = User.objects.get(id=pending_user_id, email=email, is_active=False)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid verification session'})

        # Verify OTP
        from .models import EmailOTP
        try:
            otp = EmailOTP.objects.filter(
                user=user,
                email=email,
                is_verified=False
            ).latest('created_at')

            if otp.verify(otp_code):
                # Activate the user but keep session data for final signup step
                user.is_active = True
                user.save()

                # DON'T clear session data here - keep it for final signup step
                # Session data will be cleared in handle_signup after password is set

                return JsonResponse({'success': True, 'message': 'Email verified successfully'})
            else:
                if otp.is_expired():
                    return JsonResponse({'success': False, 'message': 'Verification code has expired'})
                elif otp.attempts >= 3:
                    return JsonResponse({'success': False, 'message': 'Too many failed attempts'})
                else:
                    remaining = 3 - otp.attempts
                    return JsonResponse({'success': False, 'message': f'Invalid code. {remaining} attempts remaining'})

        except EmailOTP.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'No verification code found'})

    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
