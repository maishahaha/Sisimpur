"""
Document detector module for Sisimpur Brain.

This module provides functionality to detect document types and languages.
"""

import logging
import re
from pathlib import Path
from typing import Dict, Any

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

from ..config import MIN_TEXT_LENGTH

logger = logging.getLogger("sisimpur.detector")

def detect_question_paper(text: str, language: str) -> bool:
    """
    Detect if the text is from a question paper.

    Args:
        text: Extracted text from the document
        language: Detected language of the document

    Returns:
        True if the document appears to be a question paper, False otherwise
    """
    # Convert text to lowercase for easier pattern matching
    text_lower = text.lower()

    # First, check for Bengali patterns regardless of detected language
    # This helps with PDFs where language detection might be inaccurate

    # Look for question numbers in Bengali (১, ২, ৩, etc.)
    bengali_numbers = re.findall(r'[১২৩৪৫৬৭৮৯০]+\.', text)

    # Look for Bengali MCQ option markers (ক, খ, গ, ঘ)
    bengali_options = re.findall(r'[কখগঘ]\.', text)

    # Look for common Bengali question paper terms
    bengali_terms = [
        "প্রশ্ন", "উত্তর", "পরীক্ষা", "নম্বর", "মোট নম্বর", "সময়", "ঘন্টা", "মিনিট"
    ]

    # Count how many Bengali terms are found
    bengali_term_matches = sum(1 for term in bengali_terms if term in text)

    # If we find multiple question numbers or MCQ options, or several question paper terms
    if (len(bengali_numbers) >= 3 or len(bengali_options) >= 5 or bengali_term_matches >= 2):
        logger.info(f"Detected Bengali question paper: {len(bengali_numbers)} question numbers, "
                   f"{len(bengali_options)} options, {bengali_term_matches} question paper terms")
        return True

    # If not detected as Bengali question paper, check based on the detected language
    if language == "bengali":
        # Already checked above, but with stricter thresholds
        if (len(bengali_numbers) >= 2 or len(bengali_options) >= 3 or bengali_term_matches >= 1):
            logger.info(f"Detected Bengali question paper (lower threshold): {len(bengali_numbers)} question numbers, "
                       f"{len(bengali_options)} options, {bengali_term_matches} question paper terms")
            return True
    else:
        # English question paper patterns
        # Look for question numbers (1., 2., 3., etc.)
        question_numbers = re.findall(r'\d+\.', text)

        # Look for MCQ option markers (A., B., C., D. or a., b., c., d.)
        mcq_options = re.findall(r'[A-Da-d]\.', text)

        # Look for common English question paper terms
        english_terms = [
            "question", "answer", "exam", "test", "marks", "points", "score",
            "time", "minutes", "hours", "total marks", "section"
        ]

        # Count how many English terms are found
        term_matches = sum(1 for term in english_terms if term in text_lower)

        # If we find multiple question numbers or MCQ options, or several question paper terms
        if (len(question_numbers) >= 5 or len(mcq_options) >= 10 or term_matches >= 3):
            logger.info(f"Detected English question paper: {len(question_numbers)} question numbers, "
                       f"{len(mcq_options)} options, {term_matches} question paper terms")
            return True

    return False

def detect_document_type(file_path: str) -> Dict[str, Any]:
    """
    Detect document type and language from the given file.

    Args:
        file_path: Path to the document file

    Returns:
        Dict with document type, language, and other metadata
    """
    file_path = Path(file_path)
    file_ext = file_path.suffix.lower()

    metadata = {
        "file_path": str(file_path),
        "file_name": file_path.name,
        "file_size": file_path.stat().st_size,
        "extension": file_ext,
        "is_question_paper": False,  # Default value, will be updated if detected
    }

    # Detect document type based on extension
    if file_ext in ['.pdf']:
        metadata["doc_type"] = "pdf"

        try:
            # Use PyMuPDF (fitz) to analyze the PDF
            doc = fitz.open(file_path)

            # Initialize variables
            text_content = ""
            total_images = 0
            total_text_length = 0
            is_scanned_pdf = False

            # Check each page
            for page_num in range(len(doc)):
                page = doc[page_num]

                # Get text content
                page_text = page.get_text()
                text_content += page_text
                total_text_length += len(page_text.strip())

                # Count images
                image_list = page.get_images(full=True)
                total_images += len(image_list)

                # Check for scanned PDF indicators
                if len(image_list) > 0 and len(page_text.strip()) < 100:
                    # This page has images but little text - likely a scanned page
                    is_scanned_pdf = True

                # If this is the first page, try to detect language from it
                if page_num == 0:
                    # Try to extract text for language detection
                    sample_text = page_text

                    # If there's not enough text but there are images, try OCR on the first image
                    if len(sample_text.strip()) < 50 and len(image_list) > 0:
                        try:
                            # Extract the first image
                            xref = image_list[0][0]
                            base_image = doc.extract_image(xref)
                            image_bytes = base_image["image"]

                            # Convert to PIL Image
                            import io
                            from PIL import Image
                            image = Image.open(io.BytesIO(image_bytes))

                            # Use OCR to get sample text
                            ocr_text = pytesseract.image_to_string(image, lang='ben+eng')
                            if len(ocr_text.strip()) > len(sample_text.strip()):
                                sample_text = ocr_text
                                is_scanned_pdf = True  # If OCR gives better results, it's likely scanned
                        except Exception as e:
                            logger.warning(f"Error extracting image from PDF: {e}")

                    # Detect language from sample text
                    if len(sample_text.strip()) > 0:
                        bengali_chars = sum(1 for c in sample_text if '\u0980' <= c <= '\u09FF')
                        if bengali_chars > len(sample_text) * 0.2:  # Lower threshold for detection
                            metadata["language"] = "bengali"
                        else:
                            metadata["language"] = "english"

                        # Check if it's a question paper
                        metadata["is_question_paper"] = detect_question_paper(sample_text, metadata.get("language", "english"))

            # Determine if PDF is image-based or text-based
            # A PDF is considered image-based if:
            # 1. It has more images than pages (indicating image-heavy content)
            # 2. It has very little extractable text
            # 3. It shows signs of being a scanned document

            avg_text_per_page = total_text_length / max(1, len(doc))

            if is_scanned_pdf or total_images >= len(doc) or avg_text_per_page < 100:
                metadata["pdf_type"] = "image_based"
                logger.info(f"Detected image-based PDF: {total_images} images, {avg_text_per_page:.1f} chars/page")

                # For Bengali documents, force image-based processing for better results
                if metadata.get("language") == "bengali" and metadata.get("is_question_paper", False):
                    metadata["pdf_type"] = "image_based"
                    logger.info("Forcing image-based processing for Bengali question paper")
            else:
                metadata["pdf_type"] = "text_based"
                logger.info(f"Detected text-based PDF: {total_text_length} total chars, {avg_text_per_page:.1f} chars/page")

            # If language wasn't detected, try to detect from the full text content
            if "language" not in metadata and len(text_content.strip()) > 0:
                bengali_chars = sum(1 for c in text_content if '\u0980' <= c <= '\u09FF')
                if bengali_chars > len(text_content) * 0.2:
                    metadata["language"] = "bengali"
                else:
                    metadata["language"] = "english"

            # If question paper wasn't detected, try with the full text
            if "is_question_paper" not in metadata:
                metadata["is_question_paper"] = detect_question_paper(text_content, metadata.get("language", "english"))

            # Close the document
            doc.close()
        except Exception as e:
            logger.error(f"Error analyzing PDF: {e}")
            metadata["pdf_type"] = "unknown"
            metadata["language"] = "unknown"

    elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']:
        metadata["doc_type"] = "image"

        # Attempt to detect language (Bengali vs English)
        try:
            img = Image.open(file_path)
            # Use pytesseract to detect script
            text = pytesseract.image_to_string(img, lang='ben+eng')

            # Simple heuristic: check for Bengali Unicode range
            bengali_chars = sum(1 for c in text if '\u0980' <= c <= '\u09FF')
            if bengali_chars > len(text) * 0.3:  # If more than 30% Bengali characters
                metadata["language"] = "bengali"
            else:
                metadata["language"] = "english"

            # Detect if this is a question paper
            metadata["is_question_paper"] = detect_question_paper(text, metadata["language"])

        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            metadata["language"] = "unknown"

    else:
        metadata["doc_type"] = "unknown"

    logger.info(f"Detected document type: {metadata}")
    return metadata
