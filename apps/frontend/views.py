from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from dotenv import load_dotenv
from .utils import EmailValidationService
import requests
from requests.exceptions import SSLError, RequestException
from datetime import datetime

load_dotenv()

def is_valid_email(email):
    email_validator = EmailValidationService(
        os.getenv("MAIL_BOXLAYER_API_KEY"), os.getenv("EMAIL_VALIDATION_API_KEY")
    )
    return email_validator.is_valid_check_01(
        email
    ) or email_validator.is_valid_check_02(email)


def coming_soon(request):
    return render(request, "coming_soon/coming_soon.html")


def home(request):
    """
    View for the home page
    """
    return render(request, "home.html")


@csrf_exempt
def submit_and_subscribe(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    try:
        # Try to parse both JSON and form-encoded data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        fullname = data.get('name', '')
        email = data.get('email')
        phone = data.get('phone', '')

        if not email:
            return JsonResponse({'success': False, 'error': 'Email is required'}, status=400)

        if not is_valid_email(email):
            return JsonResponse({'success': False, 'error': 'Invalid email address'}, status=400)

        # Check if email already exists in SheetDB
        api_url = 'https://sheetdb.io/api/v1/rc0u9b8squ1ku'
        try:
            # Get all records from SheetDB
            response = requests.get(api_url)
            response.raise_for_status()
            existing_data = response.json()
            
            # Check if email already exists
            if any(record.get('email') == email for record in existing_data):
                return JsonResponse({
                    'success': False, 
                    'error': 'You are already subscribed! 🎉',
                    'title': "Welcome Back! 🐾",
                    'details': "You're already part of our amazing community. Stay tuned for more updates! ✨"
                })

            # Get current time and date
            current_datetime = datetime.now()
            current_time = current_datetime.strftime("%H:%M:%S")
            current_date = current_datetime.strftime("%Y-%m-%d")

            # Submit form to SheetDB
            payload = {
                "data": [{
                    "time": current_time,
                    "date": current_date,
                    "name": fullname,
                    "email": email,
                    "phone number": phone
                }]
            }

            sheetdb_response = requests.post(api_url, json=payload)
            sheetdb_response.raise_for_status()
            return JsonResponse({
                'success': True, 
                'message': 'Form submitted successfully',
                'title': "🎉 Welcome to Sisimpur! 🐾",
                'details': "You're now part of our amazing community. Get ready for exciting updates! ✨"
            })

        except SSLError:
            return JsonResponse({'success': False, 'error': 'SSL Error Occurred'}, status=500)
        except RequestException as e:
            return JsonResponse({'success': False, 'error': 'SheetDB request failed', 'details': str(e)}, status=500)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)