"""
Image extractors for Sisimpur Brain.

This module provides extractors for image documents.
"""

import logging
import numpy as np
import cv2
import pytesseract
from PIL import Image

from .base import BaseExtractor
from ..utils.api_utils import api
from ..config import DEFAULT_GEMINI_MODEL

logger = logging.getLogger("sisimpur.extractors.image")

class ImageExtractor(BaseExtractor):
    """Extractor for image documents"""
    
    def extract(self, file_path: str) -> str:
        """
        Extract text from image using OCR.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Extracted text
        """
        try:
            img = Image.open(file_path)
            
            # Preprocess image for better OCR
            img = self._preprocess_image(img)
            
            # Use Gemini for Bengali, pytesseract for English
            if self.language == "ben":
                text = self._extract_with_gemini(img)
            else:
                text = pytesseract.image_to_string(img, lang=self.language)
            
            temp_path = self.save_to_temp(text, file_path)
            return text
        
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            raise
    
    def _preprocess_image(self, img: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results.
        
        Args:
            img: The image to preprocess
            
        Returns:
            Preprocessed image
        """
        # Convert PIL Image to OpenCV format
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        # Resize image (scale up for better OCR)
        height, width = img_cv.shape[:2]
        img_cv = cv2.resize(img_cv, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Convert back to PIL Image
        return Image.fromarray(thresh)
    
    def _extract_with_gemini(self, img: Image.Image) -> str:
        """
        Extract text using Gemini for Bengali content.
        
        Args:
            img: The image to extract text from
            
        Returns:
            Extracted text
        """
        prompt = (
            "Extract all text from this image. Preserve original formatting and language. "
            "If the text is in Bengali, maintain the Bengali script. "
            "Return only the extracted text, no additional comments."
        )
        
        try:
            response = api.generate_content([prompt, img], model_name=DEFAULT_GEMINI_MODEL)
            return response.text
        except Exception as e:
            logger.error(f"Error using Gemini for OCR: {e}")
            # Fallback to pytesseract
            logger.info("Falling back to pytesseract for OCR")
            return pytesseract.image_to_string(img, lang='ben')
