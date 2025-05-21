import logging
import re
import numpy as np
import cv2
from PIL import Image
import easyocr

from .base import BaseExtractor
from ..utils.api_utils import api
from ..config import DEFAULT_GEMINI_MODEL

logger = logging.getLogger("sisimpur.extractors.image")


class ImageExtractor(BaseExtractor):
    """Extractor for image documents, using EasyOCR instead of Tesseract."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Map your language codes to EasyOCR’s codes:
        lang_map = {
            "ben": "bn",  # Bengali
            "eng": "en",  # English
            # add more if needed
        }
        langs = [lang_map.get(self.language, self.language)]
        # initialize once, CPU‐only
        self.reader = easyocr.Reader(langs, gpu=False)

    def extract(self, file_path: str) -> str:
        try:
            img = Image.open(file_path)
            img = self._preprocess_image(img)

            # If you still want to special-case Bengali Q-papers via Gemini:
            if self.language == "ben":
                return self._extract_with_gemini(img)
            else:
                return self._extract_with_easyocr(img)

        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            raise

    def _preprocess_image(self, img: Image.Image) -> Image.Image:
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        h, w = img_cv.shape[:2]
        img_cv = cv2.resize(img_cv, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        return Image.fromarray(thresh)

    def _extract_with_easyocr(self, img: Image.Image) -> str:
        """
        Run EasyOCR on the image and join results into a single string.
        """
        arr = np.array(img)
        # detail=0 returns only text, paragraph=True merges lines
        results = self.reader.readtext(arr, detail=0, paragraph=True)
        text = "\n".join(results)
        # optionally save to temp
        self.save_to_temp(text, None)
        return text

    # … keep your _extract_with_gemini and _is_likely_question_paper as before …

    def _extract_with_gemini(self, img: Image.Image) -> str:
        """
        Extract text using Gemini for Bengali content.

        Args:
            img: The image to extract text from

        Returns:
            Extracted text
        """
        # First, try to detect if this is a question paper using a simple heuristic
        # We'll use a small portion of the image to check
        try:
            # Get a small sample of text to check if it's a question paper
            sample_text = pytesseract.image_to_string(img, lang="ben")
            is_likely_question_paper = self._is_likely_question_paper(sample_text)
        except Exception:
            is_likely_question_paper = False

        # Use a specialized prompt for question papers
        if is_likely_question_paper:
            prompt = (
                "Extract all text from this question paper image with precise formatting. "
                "This appears to be an exam or question paper. "
                "Carefully preserve: "
                "1. Question numbers (including Bengali digits like ১, ২, ৩) "
                "2. All question text with exact wording "
                "3. Multiple choice options (ক, খ, গ, ঘ or A, B, C, D) "
                "4. Any instructions or headers "
                "Maintain original Bengali script and formatting. "
                "Return only the extracted text, no additional comments or analysis."
            )
        else:
            # Standard prompt for general content
            prompt = (
                "Extract all text from this image. Preserve original formatting and language. "
                "If the text is in Bengali, maintain the Bengali script. "
                "Return only the extracted text, no additional comments."
                "Generate questions from the text"
            )

        try:
            response = api.generate_content(
                [prompt, img], model_name=DEFAULT_GEMINI_MODEL
            )
            return response.text
        except Exception as e:
            logger.error(f"Error using Gemini for OCR: {e}")
            # Fallback to pytesseract
            logger.info("Falling back to pytesseract for OCR")
            return pytesseract.image_to_string(img, lang="ben")

    def _is_likely_question_paper(self, text: str) -> bool:
        """
        Quick check if text is likely from a question paper.

        Args:
            text: Sample text from the image

        Returns:
            True if likely a question paper, False otherwise
        """
        # Check for Bengali question numbers
        bengali_numbers = re.findall(r"[১২৩৪৫৬৭৮৯০]+\.", text)

        # Check for Bengali MCQ options
        bengali_options = re.findall(r"[কখগঘ]\.", text)

        # Check for common Bengali question paper terms
        bengali_terms = ["প্রশ্ন", "উত্তর", "পরীক্ষা", "নম্বর"]
        term_matches = sum(1 for term in bengali_terms if term in text)

        # Check for English question numbers and options too
        question_numbers = re.findall(r"\d+\.", text)
        mcq_options = re.findall(r"[A-Da-d]\.", text)

        # If we find multiple question numbers or MCQ options
        return (
            len(bengali_numbers) >= 2
            or len(bengali_options) >= 4
            or term_matches >= 2
            or len(question_numbers) >= 2
            or len(mcq_options) >= 4
        )
