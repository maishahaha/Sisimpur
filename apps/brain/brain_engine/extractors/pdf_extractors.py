"""
PDF extractors for Sisimpur Brain Engine.

This module provides extractors for PDF documents.
"""

import logging
import io
import fitz  # PyMuPDF
from PIL import Image
from pdf2image import convert_from_path

from .base import BaseExtractor
from ..utils.api_utils import api
from ..config import DEFAULT_GEMINI_MODEL
from ..utils.ocr_utils import llm_ocr_extract

logger = logging.getLogger("sisimpur.brain.extractors.pdf")

class TextPDFExtractor(BaseExtractor):
    """Extractor for text-based PDF documents"""

    def extract(self, file_path: str) -> str:
        """
        Extract text from text-based PDF.

        Args:
            file_path: Path to the PDF document

        Returns:
            Extracted text
        """
        try:
            doc = fitz.open(file_path)
            text = ""

            for page_num, page in enumerate(doc):
                text += f"--- Page {page_num + 1} ---\n"
                text += page.get_text()
                text += "\n\n"

            doc.close()
            self.save_to_temp(text, file_path)
            return text

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise


class ImagePDFExtractor(BaseExtractor):
    """Extractor for image-based PDF documents using LLM OCR"""

    def __init__(self, language: str = "eng"):
        """
        Initialize the image-based PDF extractor.

        Args:
            language: Language code for OCR (e.g., 'eng', 'ben')
        """
        super().__init__(language)
        self.lang_map = {
            "ben": "bn",
            "eng": "en",
        }
        self.llm_lang = self.lang_map.get(language, language)

    def extract(self, file_path: str) -> str:
        """
        Extract text from image-based PDF using OCR.

        Args:
            file_path: Path to the PDF document

        Returns:
            Extracted text
        """
        try:
            try:
                logger.info("Attempting to convert PDF to images using pdf2image")
                images = convert_from_path(file_path)
                return self._process_images(images, file_path)
            except Exception as pdf2image_error:
                logger.warning(f"pdf2image failed (Poppler may not installed): {pdf2image_error}")
                logger.info("Falling back to PyMuPDF for image extraction")
                return self._extract_with_pymupdf(file_path)
        except Exception as e:
            logger.error(f"Error extracting text from image-based PDF: {e}")
            raise

    def _process_images(self, images, file_path):
        """Process a list of images and extract text from them."""
        text = ""

        # Check if this is likely a question paper using LLM
        is_likely_question_paper = False
        if len(images) > 0:
            try:
                is_likely_question_paper = self._detect_question_paper(images[0])
                if is_likely_question_paper:
                    logger.info("Detected PDF as likely question paper")
            except Exception as e:
                logger.warning(f"Question paper detection failed: {e}")

        for i, img in enumerate(images):
            text += f"--- Page {i + 1} ---\n"
            try:
                # Use LLM OCR for all pages
                page_text = llm_ocr_extract(img, self.llm_lang, is_likely_question_paper)
            except Exception as e:
                logger.error(f"LLM OCR failed on page {i+1}: {e}")
                page_text = ""

            text += page_text
            text += "\n\n"

        self.save_to_temp(text, file_path)
        return text

    def _detect_question_paper(self, img: Image.Image) -> bool:
        """
        Detect if the image is likely a question paper using LLM.
        """
        try:
            prompt = (
                "Look at this image and determine if it's a question paper or exam. "
                "Answer only 'YES' if it contains questions, question numbers, or multiple choice options. "
                "Answer only 'NO' if it's regular text, notes, or other content."
            )
            response = api.generate_content([prompt, img], model_name=DEFAULT_GEMINI_MODEL)
            return response.text.strip().upper() == "YES"
        except Exception as e:
            logger.warning(f"Question paper detection failed: {e}")
            return False

    def _extract_with_pymupdf(self, file_path: str) -> str:
        """
        Extract text from PDF using PyMuPDF and LLM OCR.

        This is a fallback method when pdf2image/Poppler is not available.
        It extracts images from each PDF page and processes them with LLM OCR.

        Args:
            file_path: Path to the PDF document

        Returns:
            Extracted text
        """
        text = ""
        is_likely_question_paper = False

        try:
            # Open the PDF
            doc = fitz.open(file_path)

            # Check first page for question paper detection
            if len(doc) > 0:
                first_page = doc[0]
                # Render the first page as an image
                pix = first_page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img = Image.open(io.BytesIO(pix.tobytes("png")))

                # Check if it's a question paper using LLM
                is_likely_question_paper = self._detect_question_paper(img)
                if is_likely_question_paper:
                    logger.info("Detected PDF as likely question paper")

            # Process each page
            for page_num, page in enumerate(doc):
                text += f"--- Page {page_num + 1} ---\n"

                # Render the page as an image with high resolution
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
                img = Image.open(io.BytesIO(pix.tobytes("png")))

                # Use LLM OCR for all pages
                try:
                    page_text = llm_ocr_extract(img, self.llm_lang, is_likely_question_paper)
                except Exception as e:
                    logger.error(f"LLM OCR failed on page {page_num + 1}: {e}")
                    page_text = ""

                text += page_text
                text += "\n\n"

            # Close the document
            doc.close()

            self.save_to_temp(text, file_path)
            return text

        except Exception as e:
            logger.error(f"Error extracting with PyMuPDF: {e}")
            raise
