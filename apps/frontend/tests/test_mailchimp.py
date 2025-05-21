from django.test import TestCase, Client
from django.urls import reverse
import json


class MailchimpSubscriptionTest(TestCase):
    """Test cases for the Mailchimp subscription functionality"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()
        self.url = reverse("subscribe")

    def test_subscribe_invalid_method(self):
        """Test using an invalid HTTP method"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_subscribe_missing_email(self):
        """Test missing email in request"""
        response = self.client.post(
            self.url, json.dumps({}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "Email is required")
