import logging
from PIL import Image

logger = logging.getLogger("sisimpur.brain.utils.ocr")

from .api_utils import api
from ..config import DEFAULT_GEMINI_MODEL


def llm_ocr_extract(
    img: Image.Image,
    language_code: str = "eng",
    is_question_paper: bool = False
) -> str:
    """
    Extract text from an image using Google Gemini Vision API.

    Args:
        img: PIL Image to OCR
        language_code: Language code ('eng', 'ben', 'bn', etc.)
        is_question_paper: Whether the image is likely a question paper

    Returns:
        Extracted text

    Raises:
        RuntimeError if OCR fails
    """
    try:
        logger.info(f"Using Gemini LLM OCR with language='{language_code}'")

        # Create language-specific prompt
        if language_code.lower() in ['ben', 'bn', 'bengali']:
            if is_question_paper:
                prompt = (
                    "এই ছবি থেকে সমস্ত টেক্সট নিষ্কাশন করুন। এটি একটি প্রশ্নপত্র বলে মনে হচ্ছে। "
                    "প্রশ্ন নম্বর, প্রশ্ন, এবং উত্তরের বিকল্পগুলি সহ সমস্ত টেক্সট সংরক্ষণ করুন। "
                    "মূল বাংলা ভাষা এবং ফরম্যাটিং বজায় রাখুন। শুধুমাত্র নিষ্কাশিত টেক্সট ফেরত দিন।"
                )
            else:
                prompt = (
                    "এই ছবি থেকে সমস্ত টেক্সট নিষ্কাশন করুন। মূল বাংলা ভাষা এবং ফরম্যাটিং বজায় রাখুন। "
                    "শুধুমাত্র নিষ্কাশিত টেক্সট ফেরত দিন, কোনো অতিরিক্ত মন্তব্য নয়।"
                )
        else:
            if is_question_paper:
                prompt = (
                    "Extract all text from this image. This appears to be a question paper. "
                    "Preserve all text including question numbers, questions, and answer options. "
                    "Maintain original formatting and structure. Return only the extracted text."
                )
            else:
                prompt = (
                    "Extract all text from this image, preserving original formatting and language. "
                    "Return only the extracted text, no additional comments."
                )

        response = api.generate_content([prompt, img], model_name=DEFAULT_GEMINI_MODEL)

        if response.text.strip():
            logger.info("Gemini LLM OCR succeeded")
            return response.text.strip()
        else:
            logger.warning("Gemini LLM OCR returned empty text")
            raise RuntimeError("Gemini LLM OCR returned empty text")

    except Exception as e:
        logger.error(f"Gemini LLM OCR failed: {e}")
        raise RuntimeError(f"LLM OCR failed: {e}")


def ocr_with_fallback(
    img: Image.Image,
    language_code: str = "eng"
) -> str:
    """
    Legacy function name for backward compatibility.
    Now uses LLM-based OCR exclusively.

    Args:
        img: PIL Image to OCR
        language_code: Language code ('eng', 'ben', 'bn', etc.)

    Returns:
        Extracted text
    """
    return llm_ocr_extract(img, language_code)
