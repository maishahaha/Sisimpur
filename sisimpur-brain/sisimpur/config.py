"""
Configuration module for Sisimpur Brain.

This module handles configuration settings, environment variables,
and directory setup.
"""

import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("sisimpur")

# Base directories
BASE_DIR = Path(__file__).parent.parent
TEMP_DIR = BASE_DIR / "temp_extracts"
OUTPUT_DIR = BASE_DIR / "qa_outputs"

# Create necessary directories
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# API Keys
GEMINI_API_KEY = "AIzaSyDNh6ag0_LtAnqqARTSyGv2HVoI1A1he_g"
if not GEMINI_API_KEY:
    logger.warning("GOOGLE_API_KEY not found in environment variables. Gemini features will not work.")

# Rate limiting settings
MAX_RETRIES = 5
INITIAL_RETRY_DELAY = 2  # seconds
MAX_RETRY_DELAY = 60  # seconds
RATE_LIMIT_BATCH_SIZE = 3  # Number of chunks to process before cooling down
RATE_LIMIT_COOLDOWN = 10  # seconds between batches

# Model settings
DEFAULT_GEMINI_MODEL = "models/gemini-1.5-flash"
QA_GEMINI_MODEL = "models/gemini-1.5-flash"
FALLBACK_GEMINI_MODEL = "models/gemini-1.5-flash"  # Fallback to older model if rate limited

# Document processing settings
MIN_TEXT_LENGTH = 100  # Minimum text length to consider a PDF as text-based

# Question type settings
QUESTION_TYPE = "MULTIPLECHOICE"  # Options: "SHORT" or "MULTIPLECHOICE"
ANSWER_OPTIONS = 4  # Number of options for multiple choice questions
