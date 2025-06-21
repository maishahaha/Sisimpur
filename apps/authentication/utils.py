"""
Utility functions for authentication app
"""
import os
import requests
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def download_google_profile_picture(user, google_picture_url):
    """
    Download Google profile picture and save it to user's profile
    
    Args:
        user: User instance
        google_picture_url: URL of the Google profile picture
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not google_picture_url:
        logger.warning(f"No Google picture URL provided for user {user.username}")
        return False
    
    try:
        # Ensure user has a profile
        if not hasattr(user, 'profile'):
            from .models import UserProfile
            UserProfile.objects.create(user=user)
        
        # Store the original Google URL
        user.profile.google_picture_url = google_picture_url
        
        # Download the image
        logger.info(f"Downloading profile picture for user {user.username} from {google_picture_url}")
        
        # Add size parameter to get higher quality image
        if '?' in google_picture_url:
            picture_url = f"{google_picture_url}&sz=200"
        else:
            picture_url = f"{google_picture_url}?sz=200"
        
        response = requests.get(picture_url, timeout=10)
        response.raise_for_status()
        
        # Check if it's an image
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            logger.warning(f"Invalid content type for profile picture: {content_type}")
            user.profile.save()  # Save the Google URL even if download fails
            return False
        
        # Determine file extension
        if 'jpeg' in content_type or 'jpg' in content_type:
            ext = 'jpg'
        elif 'png' in content_type:
            ext = 'png'
        elif 'gif' in content_type:
            ext = 'gif'
        elif 'webp' in content_type:
            ext = 'webp'
        else:
            ext = 'jpg'  # Default fallback
        
        # Create filename
        filename = f"user_{user.id}_avatar.{ext}"
        
        # Save the image
        image_content = ContentFile(response.content)
        user.profile.avatar.save(filename, image_content, save=False)
        user.profile.save()
        
        logger.info(f"Successfully saved profile picture for user {user.username}")
        return True
        
    except requests.RequestException as e:
        logger.error(f"Failed to download profile picture for user {user.username}: {e}")
        # Still save the Google URL for fallback
        try:
            user.profile.save()
        except:
            pass
        return False
        
    except Exception as e:
        logger.error(f"Unexpected error saving profile picture for user {user.username}: {e}")
        return False


def ensure_media_directories():
    """
    Ensure that required media directories exist
    """
    try:
        media_root = settings.MEDIA_ROOT
        avatars_dir = os.path.join(media_root, 'avatars')
        
        # Create directories if they don't exist
        os.makedirs(avatars_dir, exist_ok=True)
        
        logger.info(f"Media directories ensured: {avatars_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create media directories: {e}")
        return False


def get_user_avatar_url(user):
    """
    Get user avatar URL with proper fallbacks
    
    Args:
        user: User instance
        
    Returns:
        str: Avatar URL
    """
    try:
        if hasattr(user, 'profile'):
            return user.profile.get_avatar_url()
        else:
            return '/static/images/default-avatar.png'
    except:
        return '/static/images/default-avatar.png'
