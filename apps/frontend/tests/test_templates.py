from django.test import TestCase
from django.template.loader import render_to_string


class TemplateTest(TestCase):
    """Test cases for the frontend app templates"""

    def test_base_template_structure(self):
        """Test that the base template has the expected structure"""
        rendered = render_to_string("base.html")

        # Check for essential HTML elements
        self.assertIn("<!DOCTYPE html>", rendered)
        self.assertIn('<html lang="en">', rendered)
        self.assertIn("<head>", rendered)
        self.assertIn("<body>", rendered)

        # Check for CSS links
        self.assertIn("bootstrap.min.css", rendered)
        self.assertIn("font-awesome", rendered)
        self.assertIn("fonts.googleapis.com", rendered)

        # Check for JS scripts
        self.assertIn("bootstrap.bundle.min.js", rendered)
        self.assertIn("main.js", rendered)

    def test_coming_soon_template_extends_base(self):
        """Test that the coming_soon template extends the base template"""
        rendered = render_to_string("coming_soon/coming_soon.html")

        # Check for content specific to coming_soon.html
        self.assertIn("SISIMPUR", rendered)
        self.assertIn("Launching Soon", rendered)
        self.assertIn("Key Features", rendered)
        self.assertIn("Join as Beta Tester", rendered)

        # Check for countdown elements
        self.assertIn("countdown-container", rendered)
        self.assertIn("countdown-item", rendered)
        self.assertIn('id="days"', rendered)
        self.assertIn('id="hours"', rendered)
        self.assertIn('id="minutes"', rendered)
        self.assertIn('id="seconds"', rendered)
