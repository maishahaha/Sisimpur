"""
Document detector module for Sisimpur Brain.

This module provides functionality to detect document types and languages.
"""

import logging
import re
import io
from pathlib import Path
from typing import Dict, Any

import fitz  # PyMuPDF
from PIL import Image
import numpy as np
import easyocr

from ..config import MIN_TEXT_LENGTH

logger = logging.getLogger("sisimpur.detector")

# Initialize EasyOCR reader once (English and Bengali)
OCR_LANGUAGES = ["en", "bn"]
reader = easyocr.Reader(OCR_LANGUAGES, gpu=False)


def detect_language(text: str) -> str:
    """
    Robust language detection with better Bengali support.

    Args:
        text: Text to analyze

    Returns:
        'bengali' or 'english'
    """
    if not text.strip():
        return "english"  # default

    # Count Bengali Unicode characters
    bengali_chars = sum(1 for c in text if "\u0980" <= c <= "\u09ff")
    total_chars = max(1, len(text))
    ratio = bengali_chars / total_chars

    # Common Bengali words that might appear even in short texts
    bengali_keywords = ["প্রশ্ন", "উত্তর", "নম্বর", "সময়", "বাংলা"]

    # Detection rules:
    # 1. If we find at least 5 Bengali chars AND either:
    #    a) Over 7% Bengali characters, OR
    #    b) Any Bengali keywords present
    if bengali_chars >= 5 and (
        ratio > 0.07 or any(keyword in text for keyword in bengali_keywords)
    ):
        return "bengali"

    return "english"


def detect_question_paper(text: str, language: str) -> bool:
    """
    Enhanced question paper detection with better Bengali support.
    """
    text_lower = text.lower()

    # Bengali patterns
    bengali_numbers = re.findall(r"[১২৩৪৫৬৭৮৯০]+\.", text)
    bengali_options = re.findall(r"[কখগঘ]\.", text)

    bengali_terms = [
        "প্রশ্ন",
        "উত্তর",
        "পরীক্ষা",
        "নম্বর",
        "মোট নম্বর",
        "সময়",
        "ঘন্টা",
        "মিনিট",
        "পাঠ্যক্রম",
        "বিষয়",
        "পর্ব",
    ]

    bengali_term_matches = sum(1 for term in bengali_terms if term in text)

    # Bengali detection thresholds
    if (
        len(bengali_numbers) >= 2
        or len(bengali_options) >= 3
        or bengali_term_matches >= 1
    ):
        logger.info("Detected Bengali question paper")
        return True

    # English patterns (only check if not Bengali)
    if language != "bengali":
        question_numbers = re.findall(r"\d+\.", text)
        mcq_options = re.findall(r"[A-Da-d]\.", text)

        english_terms = [
            "question",
            "answer",
            "exam",
            "test",
            "marks",
            "points",
            "score",
            "time",
            "minutes",
            "hours",
            "total marks",
            "section",
        ]

        term_matches = sum(1 for term in english_terms if term in text_lower)

        if len(question_numbers) >= 3 or len(mcq_options) >= 5 or term_matches >= 2:
            logger.info("Detected English question paper")
            return True

    return False


def detect_document_type(file_path: str) -> Dict[str, Any]:
    """
    Enhanced document type detection with improved language handling.
    """
    file_path = Path(file_path)
    file_ext = file_path.suffix.lower()

    metadata = {
        "file_path": str(file_path),
        "file_name": file_path.name,
        "file_size": file_path.stat().st_size,
        "extension": file_ext,
        "is_question_paper": False,
        "doc_type": "unknown",
        "language": "english",  # Default to English
        "pdf_type": "unknown" if file_ext == ".pdf" else None,
    }

    try:
        if file_ext == ".pdf":
            metadata["doc_type"] = "pdf"
            doc = fitz.open(file_path)

            text_content = ""
            total_images = 0
            total_text_length = 0
            is_scanned_pdf = False

            for page_num in range(min(3, len(doc))):  # Check first 3 pages
                page = doc[page_num]
                page_text = page.get_text()
                text_content += page_text
                total_text_length += len(page_text.strip())

                image_list = page.get_images(full=True)
                total_images += len(image_list)

                # Scanned PDF check
                if len(image_list) > 0 and len(page_text.strip()) < 50:
                    is_scanned_pdf = True

                    # OCR on first image using EasyOCR
                    try:
                        xref = image_list[0][0]
                        base_image = doc.extract_image(xref)
                        image = Image.open(io.BytesIO(base_image["image"]))
                        img_array = np.array(image)
                        ocr_results = reader.readtext(
                            img_array, detail=0, paragraph=True
                        )
                        ocr_text = "\n".join(ocr_results)

                        if len(ocr_text.strip()) > len(page_text.strip()):
                            text_content += "\n" + ocr_text
                    except Exception as e:
                        logger.warning(f"OCR error: {e}")

                # Early language detection
                if page_num == 0 and text_content.strip():
                    metadata["language"] = detect_language(text_content)

            # Final language determination
            if text_content.strip():
                metadata["language"] = detect_language(text_content)

            # Question paper detection
            metadata["is_question_paper"] = detect_question_paper(
                text_content, metadata["language"]
            )

            # PDF type classification
            avg_text_per_page = total_text_length / max(1, len(doc))

            if is_scanned_pdf or total_images >= len(doc) or avg_text_per_page < 100:
                metadata["pdf_type"] = "image_based"
            else:
                metadata["pdf_type"] = "text_based"

            doc.close()

        elif file_ext in [".jpg", ".jpeg", ".png"]:
            metadata["doc_type"] = "image"
            img = Image.open(file_path)
            img_array = np.array(img)

            # OCR with EasyOCR
            ocr_results = reader.readtext(img_array, detail=0, paragraph=True)
            ocr_text = "\n".join(ocr_results)

            metadata["language"] = detect_language(ocr_text)
            metadata["is_question_paper"] = detect_question_paper(
                ocr_text, metadata["language"]
            )
    except Exception as e:
        logger.error(f"Document processing error: {e}")

    logger.info(f"Final document metadata: {metadata}")
    return metadata
