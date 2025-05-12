from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import os
from dotenv import load_dotenv
from .utils import MailchimpService
from pathlib import Path
import requests

load_dotenv()
env_path = Path(__file__).resolve().parent.parent / '.env'
# Load the .env from the root directory
load_dotenv(dotenv_path=env_path)

def is_valid_email_by_check01(email):
    url = "http://apilayer.net/api/check"
    params = {
        "access_key": "6cb1b53c3055ade26f8a5f739fd774a2",
        "email": email,
        "smtp": 1,
        "format": 1,
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        return data.get("smtp_check", False)
    except requests.RequestException:
        return False

def is_valid_email_by_check02(email):
    url = "https://api.emailvalidation.io/v1/info"
    params = {
        "apikey": "ema_live_XBp8pY8ctIqMHBcHhJqgxJ6HVZUhJt3ic6pSbs2K",
        "email": email,
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        return data.get("smtp_check", False)
    except requests.RequestException:
        return False

def is_valid_email(email):
    return is_valid_email_by_check01(email) or is_valid_email_by_check02(email)

def index(request):
    return render(request, 'index.html')

@csrf_exempt
def subscribe_to_mailchimp(request):
    """
    API endpoint to subscribe an email to Mailchimp list
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method is allowed'}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get('email')

        if not email:
            return JsonResponse({'success': False, 'error': 'Email is required'}, status=400)

        #check if email is valid
        if not is_valid_email(email):
            return JsonResponse({'success': False, 'error': 'Invalid email address'}, status=400)


        # Initialize Mailchimp service
        api_key = os.getenv("MAILCHIMP_API_KEY")  # Your Mailchimp API key
        server_prefix = 'us13'  # Extract from API key

        # In production, you should store these in settings or environment variables
        # You need to create a list in Mailchimp and get its ID
        # For now, we'll try to get the first list from the account
        mailchimp = MailchimpService(api_key, server_prefix)

        try:
            # Try to get the first list from the account
            response = mailchimp.client.lists.get_all_lists()
            if response["lists"] and len(response["lists"]) > 0:
                list_id = response["lists"][0]["id"]
            else:
                # If no lists found, return an error
                return JsonResponse({
                    'success': False,
                    'error': 'No Mailchimp lists found. Please create a list in your Mailchimp account.'
                }, status=500)
        except Exception as e:
            # If there's an error getting lists, use a placeholder for testing
            # In production, this should be handled more gracefully
            return JsonResponse({
                'success': False,
                'error': f'Error connecting to Mailchimp: {str(e)}'
            }, status=500)

        # Add subscriber to the list
        # Use "subscribed" status to skip the confirmation email
        result = mailchimp.add_subscriber(list_id, email, status="subscribed")

        if result['success']:
            return JsonResponse({'success': True, 'message': 'Thank you for subscribing!'})
        else:
            return JsonResponse({'success': False, 'error': result['error']}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
