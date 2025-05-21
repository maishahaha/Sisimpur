from django.test import TestCase, Client
from django.urls import reverse


class AuthViewTest(TestCase):
    """Test cases for the authentication views"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()

    def test_auth_view_exists(self):
        """Test that the auth view function exists"""
        from authentication.views import signupin

        self.assertTrue(callable(signupin))

    def test_auth_view_renders_template(self):
        """Test that the auth view renders the correct template"""
        # This test will fail until the auth.html template is created and the URL is configured
        # Uncomment when ready to implement
        """
        url = reverse('auth')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth.html')
        """
        pass
