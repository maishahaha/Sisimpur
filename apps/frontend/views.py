from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import datetime
import json
import os
from dotenv import load_dotenv
from .utils import EmailValidationService
import requests
from requests.exceptions import SSLError, RequestException

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

        # SheetDB API configuration
        api_url = 'https://sheetdb.io/api/v1/rc0u9b8squ1ku'
        headers = {
            'Authorization': f'Bearer {os.getenv("SHEETDB_API_KEY")}',
            'Content-Type': 'application/json'
        }

        try:
            # Get all records from SheetDB
            response = requests.get(api_url, headers=headers, timeout=10)
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

            sheetdb_response = requests.post(api_url, headers=headers, json=payload, timeout=10)
            sheetdb_response.raise_for_status()
            
            # Log successful submission
            print(f"Successfully submitted data to SheetDB for email: {email}")
            
            return JsonResponse({
                'success': True, 
                'message': "You're now part of our amazing community. Get ready for exciting updates! ✨",
                'title': "🎉 Welcome to Sisimpur! 🐾"
            })

        except SSLError as ssl_err:
            print(f"SSL Error occurred: {str(ssl_err)}")
            return JsonResponse({
                'success': False, 
                'error': 'SSL Error Occurred', 
                'details': 'There was a problem with the secure connection. Please try again later.'
            }, status=500)
        except requests.Timeout:
            print("Request timed out while connecting to SheetDB")
            return JsonResponse({
                'success': False, 
                'error': 'Request timed out',
                'details': 'The request took too long to complete. Please try again later.'
            }, status=500)
        except RequestException as e:
            print(f"SheetDB request failed: {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': 'SheetDB request failed',
                'details': 'Unable to connect to the database. Please try again later.'
            }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print(f"Unexpected error in submit_and_subscribe: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': 'An unexpected error occurred',
            'details': 'Please try again later or contact support if the problem persists.'
        }, status=500)


def health_check(request):
    """
    Simple health check endpoint for load balancer
    """
    print("Health check endpoint accessed")
    return HttpResponse("OK", status=200)