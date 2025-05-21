import logging
from .utils.api_utils import api
from .config import DEFAULT_GEMINI_MODEL, FALLBACK_GEMINI_MODEL

logger = logging.getLogger("sisimpur.model_client")


class ModelClient:
    def __init__(
        self, primary: str = DEFAULT_GEMINI_MODEL, fallback: str = FALLBACK_GEMINI_MODEL
    ):
        self.primary = primary
        self.fallback = fallback

    def generate(self, prompt, data=None):
        payload = [prompt, data] if data is not None else prompt
        try:
            return api.generate_content(payload, model_name=self.primary)
        except Exception as e:
            logger.warning(
                f"Primary model failed: {e}. Falling back to {self.fallback}"
            )
            return api.generate_content(payload, model_name=self.fallback)
