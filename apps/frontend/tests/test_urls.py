from django.test import SimpleTestCase
from django.urls import reverse, resolve
from frontend.views import coming_soon


class UrlsTest(SimpleTestCase):
    """Test cases for the frontend app URLs"""

    def test_coming_soon_url_resolves(self):
        """Test that the coming_soon URL resolves to the correct view function"""
        url = reverse('coming_soon')
        self.assertEqual(resolve(url).func, coming_soon)

    def test_coming_soon_url_name(self):
        """Test that the coming_soon URL name resolves to the correct path"""
        url = reverse('coming_soon')
        self.assertEqual(url, '/coming-soon/')
