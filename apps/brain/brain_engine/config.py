"""
Configuration module for Sisimpur Brain Engine.

This module handles configuration settings, environment variables,
and directory setup.
"""

import os
import logging
from pathlib import Path
from django.conf import settings

# Configure logging
logger = logging.getLogger("sisimpur.brain")

class BrainConfig:
    """Configuration class for Brain Engine"""
    
    def __init__(self):
        # Get configuration from Django settings
        self.config = getattr(settings, 'BRAIN_CONFIG', {})
        
        # Base directories
        self.BASE_DIR = Path(settings.BASE_DIR)
        self.TEMP_DIR = getattr(settings, 'BRAIN_TEMP_DIR', self.BASE_DIR / 'media' / 'brain' / 'temp_extracts')
        self.OUTPUT_DIR = getattr(settings, 'BRAIN_OUTPUT_DIR', self.BASE_DIR / 'media' / 'brain' / 'qa_outputs')
        self.UPLOADS_DIR = getattr(settings, 'BRAIN_UPLOADS_DIR', self.BASE_DIR / 'media' / 'brain' / 'uploads')
        
        # Create necessary directories
        self.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        
        # API Keys
        self.GEMINI_API_KEY = self.config.get('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not self.GEMINI_API_KEY:
            logger.warning(
                "GOOGLE_API_KEY not found in environment variables. Gemini features will not work."
            )
        
        # Rate limiting settings
        self.MAX_RETRIES = self.config.get('MAX_RETRIES', 5)
        self.INITIAL_RETRY_DELAY = self.config.get('INITIAL_RETRY_DELAY', 2)  # seconds
        self.MAX_RETRY_DELAY = self.config.get('MAX_RETRY_DELAY', 60)  # seconds
        self.RATE_LIMIT_BATCH_SIZE = self.config.get('RATE_LIMIT_BATCH_SIZE', 3)  # Number of chunks to process before cooling down
        self.RATE_LIMIT_COOLDOWN = self.config.get('RATE_LIMIT_COOLDOWN', 10)  # seconds between batches
        
        # Model settings
        self.DEFAULT_GEMINI_MODEL = self.config.get('DEFAULT_GEMINI_MODEL', "models/gemini-1.5-flash")
        self.QA_GEMINI_MODEL = self.config.get('QA_GEMINI_MODEL', "models/gemini-1.5-flash")
        self.FALLBACK_GEMINI_MODEL = self.config.get('FALLBACK_GEMINI_MODEL', "models/gemini-1.5-flash")
        
        # Document processing settings
        self.MIN_TEXT_LENGTH = self.config.get('MIN_TEXT_LENGTH', 100)  # Minimum text length to consider a PDF as text-based
        
        # Question type settings
        self.QUESTION_TYPE = self.config.get('QUESTION_TYPE', "MULTIPLECHOICE")  # Options: "SHORT" or "MULTIPLECHOICE"
        self.ANSWER_OPTIONS = self.config.get('ANSWER_OPTIONS', 4)  # Number of options for multiple choice questions

# Global configuration instance
config = BrainConfig()

# Export commonly used values for backward compatibility
GEMINI_API_KEY = config.GEMINI_API_KEY
MAX_RETRIES = config.MAX_RETRIES
INITIAL_RETRY_DELAY = config.INITIAL_RETRY_DELAY
MAX_RETRY_DELAY = config.MAX_RETRY_DELAY
RATE_LIMIT_BATCH_SIZE = config.RATE_LIMIT_BATCH_SIZE
RATE_LIMIT_COOLDOWN = config.RATE_LIMIT_COOLDOWN
DEFAULT_GEMINI_MODEL = config.DEFAULT_GEMINI_MODEL
QA_GEMINI_MODEL = config.QA_GEMINI_MODEL
FALLBACK_GEMINI_MODEL = config.FALLBACK_GEMINI_MODEL
MIN_TEXT_LENGTH = config.MIN_TEXT_LENGTH
QUESTION_TYPE = config.QUESTION_TYPE
ANSWER_OPTIONS = config.ANSWER_OPTIONS
TEMP_DIR = config.TEMP_DIR
OUTPUT_DIR = config.OUTPUT_DIR
UPLOADS_DIR = config.UPLOADS_DIR
