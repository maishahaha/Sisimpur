"""
Extractors for Sisimpur Brain.
"""

# from .base import BaseExtractor
# from .pdf_extractors import TextPDFExtractor, ImagePDFExtractor
# from .image_extractors import ImageExtractor
from .ocr_factory import get_extractor

__all__ = [
    'get_extractor'
]
