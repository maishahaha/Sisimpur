import logging
from PIL import Image
import numpy as np

logger = logging.getLogger("sisimpur.brain.utils.ocr")

import easyocr
from .api_utils import api
from ..config import DEFAULT_GEMINI_MODEL

# EasyOCR reader will be initialized when needed
_EASYOCR_LANGS = ['en', 'bn']
_easyocr_reader = None


def get_easyocr_reader():
    """Get or initialize the EasyOCR reader."""
    global _easyocr_reader
    if _easyocr_reader is None:
        _easyocr_reader = easyocr.Reader(_EASYOCR_LANGS, gpu=False)
    return _easyocr_reader


def ocr_with_fallback(
    img: Image.Image,
    language_code: str = "eng"
) -> str:
    """
    Extract text from an image using EasyOCR.
    If EasyOCR fails or returns empty, fallback to Gemini LLM OCR.

    Args:
        img: PIL Image to OCR
        language_code: Language code ('eng', 'ben', 'bn', etc.)

    Returns:
        Extracted text

    Raises:
        RuntimeError if all methods fail
    """
    lang_map_easyocr = {
        "eng": "en",
        "ben": "bn",
        "bn": "bn",
        "bengali": "bn"
    }
    easyocr_lang = lang_map_easyocr.get(language_code.lower(), "en")

    # Try EasyOCR
    try:
        logger.info(f"Trying EasyOCR with lang='{easyocr_lang}'")
        arr = np.array(img)
        reader = get_easyocr_reader()
        results = reader.readtext(arr, detail=0, paragraph=True)
        text = "\n".join(results)
        if text.strip():
            logger.info("EasyOCR succeeded")
            return text
        else:
            logger.info("EasyOCR returned empty text, trying fallback")
    except Exception as e:
        logger.warning(f"EasyOCR failed: {e}")

    # Fallback Gemini LLM OCR
    try:
        logger.info("Trying Gemini LLM OCR fallback")
        prompt = (
            "Extract all text from this image, preserving formatting and language. "
            "Return only the extracted text."
        )
        response = api.generate_content([prompt, img], model_name=DEFAULT_GEMINI_MODEL)
        if response.text.strip():
            logger.info("Gemini LLM OCR succeeded")
            return response.text
        else:
            logger.warning("Gemini LLM OCR returned empty text")
    except Exception as e:
        logger.error(f"Gemini LLM OCR fallback failed: {e}")

    raise RuntimeError("All OCR methods failed to extract text")
