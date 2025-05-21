from django.test import TestCase
from django.contrib.auth.models import User


class UserModelTest(TestCase):
    """Test cases for the User model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword123"
        )

    def test_user_creation(self):
        """Test that a user can be created"""
        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(self.user.email, "test@example.com")
        self.assertTrue(self.user.check_password("testpassword123"))

    def test_user_string_representation(self):
        """Test the string representation of a user"""
        self.assertEqual(str(self.user), "testuser")

    def test_user_is_active_by_default(self):
        """Test that a user is active by default"""
        self.assertTrue(self.user.is_active)

    def test_user_is_not_staff_by_default(self):
        """Test that a user is not staff by default"""
        self.assertFalse(self.user.is_staff)

    def test_user_is_not_superuser_by_default(self):
        """Test that a user is not a superuser by default"""
        self.assertFalse(self.user.is_superuser)
