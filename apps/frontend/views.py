from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import os
from .utils import MailchimpService

# Create your views here.

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

        # Initialize Mailchimp service
        api_key = 'c142e8c1d822a5f26d36f3e2ef6bc60e-us13'  # Your Mailchimp API key
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
