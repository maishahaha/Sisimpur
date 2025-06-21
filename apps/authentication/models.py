from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.db.models.signals import post_save
from django.dispatch import receiver
import random
import string
import hashlib
import os

class EmailOTP(models.Model):
    """Model to store email OTP for verification with security best practices"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_otps')
    email = models.EmailField()
    otp_hash = models.CharField(max_length=128)  # Store hashed OTP, not plain text
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    ip_address = models.GenericIPAddressField(null=True, blank=True)  # Track IP for security

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email OTP'
        verbose_name_plural = 'Email OTPs'
        indexes = [
            models.Index(fields=['email', 'created_at']),
            models.Index(fields=['user', 'is_verified']),
        ]

    def __str__(self):
        return f"OTP for {self.email} - Created: {self.created_at}"

    @classmethod
    def generate_otp(cls, user, email, ip_address=None):
        """Generate a new secure OTP for user email"""
        # Invalidate any existing OTPs for this user/email
        cls.objects.filter(user=user, email=email, is_verified=False).update(is_verified=True)

        # Generate OTP code
        otp_length = settings.OTP_CONFIG.get('OTP_LENGTH', 6)
        otp_code = ''.join(random.choices(string.digits, k=otp_length))

        # Hash the OTP for secure storage
        otp_hash = hashlib.sha256(otp_code.encode()).hexdigest()

        # Calculate expiry time (shorter for security)
        expiry_minutes = settings.OTP_CONFIG.get('OTP_EXPIRY_MINUTES', 5)  # Reduced to 5 minutes
        expires_at = timezone.now() + timezone.timedelta(minutes=expiry_minutes)

        # Create new OTP
        otp_instance = cls.objects.create(
            user=user,
            email=email,
            otp_hash=otp_hash,
            expires_at=expires_at,
            ip_address=ip_address
        )

        # Return both instance and plain OTP (for email sending only)
        otp_instance._plain_otp = otp_code  # Temporary attribute, not stored
        return otp_instance

    def is_expired(self):
        """Check if OTP is expired"""
        return timezone.now() > self.expires_at

    def is_valid(self):
        """Check if OTP is valid (not expired, not verified, not exceeded attempts)"""
        max_attempts = settings.OTP_CONFIG.get('MAX_OTP_ATTEMPTS', 3)
        return (
            not self.is_expired() and
            not self.is_verified and
            self.attempts < max_attempts
        )

    def verify(self, entered_otp):
        """Verify the entered OTP using secure hash comparison"""
        self.attempts += 1
        self.save()

        if not self.is_valid():
            return False

        # Hash the entered OTP and compare with stored hash
        entered_hash = hashlib.sha256(entered_otp.encode()).hexdigest()

        if self.otp_hash == entered_hash:
            self.is_verified = True
            self.save()
            return True

        return False

    @classmethod
    def cleanup_expired(cls):
        """Clean up expired OTPs (call this periodically)"""
        expired_count = cls.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()[0]
        return expired_count

class OTPRateLimit(models.Model):
    """Model to track OTP request rate limiting"""

    email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    attempts = models.PositiveIntegerField(default=1)
    first_attempt = models.DateTimeField(auto_now_add=True)
    last_attempt = models.DateTimeField(auto_now=True)
    is_blocked = models.BooleanField(default=False)
    blocked_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['email', 'ip_address']
        verbose_name = 'OTP Rate Limit'
        verbose_name_plural = 'OTP Rate Limits'
        indexes = [
            models.Index(fields=['email', 'ip_address']),
            models.Index(fields=['blocked_until']),
        ]

    def __str__(self):
        return f"Rate limit for {self.email} from {self.ip_address}"

    @classmethod
    def check_rate_limit(cls, email, ip_address):
        """Check if email/IP combination is rate limited"""
        now = timezone.now()
        hour_ago = now - timezone.timedelta(hours=1)

        # Get or create rate limit record
        rate_limit, created = cls.objects.get_or_create(
            email=email,
            ip_address=ip_address,
            defaults={'attempts': 0}
        )

        # Check if currently blocked
        if rate_limit.is_blocked and rate_limit.blocked_until and now < rate_limit.blocked_until:
            return False, f"Too many attempts. Try again after {rate_limit.blocked_until.strftime('%H:%M')}"

        # Reset if block period expired
        if rate_limit.is_blocked and rate_limit.blocked_until and now >= rate_limit.blocked_until:
            rate_limit.is_blocked = False
            rate_limit.blocked_until = None
            rate_limit.attempts = 0
            rate_limit.save()

        # Reset attempts if more than 1 hour passed
        if rate_limit.first_attempt < hour_ago:
            rate_limit.attempts = 0
            rate_limit.first_attempt = now

        # Check rate limit (5 attempts per hour)
        max_attempts = settings.OTP_CONFIG.get('MAX_HOURLY_ATTEMPTS', 5)
        if rate_limit.attempts >= max_attempts:
            # Block for 1 hour
            rate_limit.is_blocked = True
            rate_limit.blocked_until = now + timezone.timedelta(hours=1)
            rate_limit.save()
            return False, "Too many OTP requests. Please try again in 1 hour."

        # Increment attempts
        rate_limit.attempts += 1
        rate_limit.last_attempt = now
        rate_limit.save()

        return True, "OK"

    @classmethod
    def cleanup_old_records(cls):
        """Clean up old rate limit records"""
        week_ago = timezone.now() - timezone.timedelta(days=7)
        deleted_count = cls.objects.filter(
            last_attempt__lt=week_ago,
            is_blocked=False
        ).delete()[0]
        return deleted_count


def user_avatar_path(instance, filename):
    """Generate upload path for user avatars"""
    # Get file extension
    ext = filename.split('.')[-1]
    # Create filename: user_id_avatar.ext
    filename = f"user_{instance.user.id}_avatar.{ext}"
    # Return path: media/avatars/user_id_avatar.ext
    return os.path.join('avatars', filename)


class UserProfile(models.Model):
    """Extended user profile with additional fields"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(
        upload_to=user_avatar_path,
        null=True,
        blank=True,
        help_text="User profile picture"
    )
    google_picture_url = models.URLField(
        null=True,
        blank=True,
        help_text="Original Google profile picture URL"
    )
    bio = models.TextField(
        max_length=500,
        null=True,
        blank=True,
        help_text="User biography"
    )
    location = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="User location"
    )
    website = models.URLField(
        null=True,
        blank=True,
        help_text="User website"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_avatar_url(self):
        """Get avatar URL with fallback to default"""
        if self.avatar:
            return self.avatar.url
        elif self.google_picture_url:
            return self.google_picture_url
        else:
            return '/static/images/default-avatar.png'

    def has_avatar(self):
        """Check if user has an avatar"""
        return bool(self.avatar or self.google_picture_url)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created"""
    if created:
        try:
            UserProfile.objects.create(user=instance)
        except Exception:
            # Handle case where UserProfile table doesn't exist (e.g., during tests)
            pass


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    try:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            UserProfile.objects.create(user=instance)
    except Exception:
        # Handle case where UserProfile table doesn't exist (e.g., during tests)
        pass
