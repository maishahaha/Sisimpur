"""
Utilities for Sisimpur Brain.
"""

from .document_detector import detect_document_type
from .api_utils import api
from .file_utils import save_extracted_text, save_qa_pairs, load_qa_pairs

__all__ = [
    'detect_document_type',
    'api',
    'save_extracted_text',
    'save_qa_pairs',
    'load_qa_pairs',
]
