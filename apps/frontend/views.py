from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from dotenv import load_dotenv
from .utils import MailchimpService, EmailValidationService
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

        # Submit form to SheetDB
        api_url = 'https://sheetdb.io/api/v1/rc0u9b8squ1ku'
        payload = {
            "data": {
                "fullname": fullname,
                "email": email,
                "phone": phone
            }
        }

        try:
            sheetdb_response = requests.post(api_url, json=payload)
            sheetdb_response.raise_for_status()
        except SSLError:
            return JsonResponse({'success': False, 'error': 'SSL Error Occurred'}, status=500)
        except RequestException as e:
            return JsonResponse({'success': False, 'error': 'SheetDB request failed', 'details': str(e)}, status=500)

        # Subscribe to Mailchimp
        api_key = os.getenv("MAILCHIMP_API_KEY")
        server_prefix = "us13"  # Adjust this based on your actual Mailchimp API key
        mailchimp = MailchimpService(api_key, server_prefix)

        try:
            response = mailchimp.client.lists.get_all_lists()
            if response["lists"] and len(response["lists"]) > 0:
                list_id = response["lists"][0]["id"]
            else:
                return JsonResponse({'success': False, 'error': 'No Mailchimp lists found'}, status=500)
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Mailchimp connection error: {str(e)}'}, status=500)

        result = mailchimp.add_subscriber(list_id, email, status="subscribed")
        if not result["success"]:
            return JsonResponse({'success': False, 'error': result["error"]}, status=400)

        return JsonResponse({
            'success': True,
            'message': 'Form submitted and subscribed successfully',
            'title': "🎉 Yay! You're part of the Sisimpur Circle 🐾",
            'details': "Early access? ✅ Secret features? ✅ Big hugs from the team 💛 Let the magic begin! ✨🌈"
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)