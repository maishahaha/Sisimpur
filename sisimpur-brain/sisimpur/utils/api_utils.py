"""
API utilities for Sisimpur Brain.

This module provides utilities for API calls with rate limiting and retries.
"""

import time
import logging
import random
from typing import Any, Callable, Dict, List, Optional, Union

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable

from ..config import (
    GEMINI_API_KEY,
    MAX_RETRIES,
    INITIAL_RETRY_DELAY,
    MAX_RETRY_DELAY,
    RATE_LIMIT_BATCH_SIZE,
    RATE_LIMIT_COOLDOWN,
    DEFAULT_GEMINI_MODEL,
    QA_GEMINI_MODEL,
    FALLBACK_GEMINI_MODEL,
)

logger = logging.getLogger("sisimpur.api")

# Configure Gemini API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class RateLimitedAPI:
    """
    A utility class for making rate-limited API calls with retries and backoff.
    """

    def __init__(self):
        self.request_count = 0
        self.last_cooldown = time.time()
        self.models_cache = {}

    def get_model(
        self, model_name: str = DEFAULT_GEMINI_MODEL
    ) -> genai.GenerativeModel:
        """Get a cached model instance or create a new one"""
        if model_name not in self.models_cache:
            self.models_cache[model_name] = genai.GenerativeModel(model_name)
        return self.models_cache[model_name]

    def with_rate_limit(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with rate limiting and retries.

        Args:
            func: The function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            The result of the function call
        """
        # Check if we need to cool down
        self.request_count += 1
        if self.request_count >= RATE_LIMIT_BATCH_SIZE:
            time_since_cooldown = time.time() - self.last_cooldown
            if time_since_cooldown < RATE_LIMIT_COOLDOWN:
                cooldown_time = RATE_LIMIT_COOLDOWN - time_since_cooldown
                logger.info(
                    f"Rate limit cooldown: sleeping for {cooldown_time:.2f} seconds"
                )
                time.sleep(cooldown_time)
            self.request_count = 0
            self.last_cooldown = time.time()

        # Try with retries and exponential backoff
        retry_count = 0
        retry_delay = INITIAL_RETRY_DELAY

        while True:
            try:
                return func(*args, **kwargs)

            except (ResourceExhausted, ServiceUnavailable) as e:
                retry_count += 1
                if retry_count > MAX_RETRIES:
                    logger.error(f"Max retries ({MAX_RETRIES}) exceeded: {e}")
                    raise

                # Add jitter to avoid thundering herd
                jitter = random.uniform(0.8, 1.2)
                sleep_time = retry_delay * jitter

                logger.warning(
                    f"Rate limit hit, retrying in {sleep_time:.2f} seconds "
                    f"(attempt {retry_count}/{MAX_RETRIES}): {e}"
                )

                time.sleep(sleep_time)
                retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)

            except Exception as e:
                logger.error(f"Error in API call: {e}")
                raise

    def generate_content(
        self,
        prompt: Union[str, List],
        model_name: str = DEFAULT_GEMINI_MODEL,
        fallback: bool = True,
    ) -> Any:
        """
        Generate content with rate limiting and retries.

        Args:
            prompt: The prompt to send to the model
            model_name: The name of the model to use
            fallback: Whether to try fallback models if rate limited

        Returns:
            The model's response
        """
        model = self.get_model(model_name)

        try:
            return self.with_rate_limit(model.generate_content, prompt)

        except ResourceExhausted as e:
            if fallback and model_name != FALLBACK_GEMINI_MODEL:
                logger.warning(
                    f"Falling back to {FALLBACK_GEMINI_MODEL} due to rate limits"
                )
                fallback_model = self.get_model(FALLBACK_GEMINI_MODEL)
                return self.with_rate_limit(fallback_model.generate_content, prompt)
            else:
                raise


# Create a singleton instance
api = RateLimitedAPI()
