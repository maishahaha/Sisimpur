"""
Document detector module for Sisimpur Brain.

This module provides functionality to detect document types and languages.
"""

import logging
from pathlib import Path
from typing import Dict, Any

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

from ..config import MIN_TEXT_LENGTH

logger = logging.getLogger("sisimpur.detector")

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
    }
    
    # Detect document type based on extension
    if file_ext in ['.pdf']:
        metadata["doc_type"] = "pdf"
        # Check if PDF is text-based or image-based
        try:
            doc = fitz.open(file_path)
            text_content = ""
            for page in doc:
                text_content += page.get_text()
            
            if len(text_content.strip()) > MIN_TEXT_LENGTH:  # If substantial text is extracted
                metadata["pdf_type"] = "text_based"
            else:
                metadata["pdf_type"] = "image_based"
            
            # Close the document
            doc.close()
        except Exception as e:
            logger.error(f"Error analyzing PDF: {e}")
            metadata["pdf_type"] = "unknown"
    
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
        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            metadata["language"] = "unknown"
    
    else:
        metadata["doc_type"] = "unknown"
    
    logger.info(f"Detected document type: {metadata}")
    return metadata
