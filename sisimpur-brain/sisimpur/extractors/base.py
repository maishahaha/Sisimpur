"""
Base extractor module for Sisimpur Brain.

This module provides the base class for all document extractors.
"""

import logging
from abc import ABC, abstractmethod

from ..utils.file_utils import save_extracted_text

logger = logging.getLogger("sisimpur.extractors")


class BaseExtractor(ABC):
    """Base class for all document extractors"""

    def __init__(self, language: str = "eng"):
        """
        Initialize the extractor.

        Args:
            language: The language code (e.g., 'eng', 'ben')
        """
        self.language = language

    @abstractmethod
    def extract(self, file_path: str) -> str:
        """
        Extract text from document.

        Args:
            file_path: Path to the document

        Returns:
            Extracted text
        """
        pass

    def save_to_temp(self, text: str, file_path: str) -> str:
        """
        Save extracted text to temporary file.

        Args:
            text: Extracted text
            file_path: Path to the source document

        Returns:
            Path to the saved file
        """
        return save_extracted_text(text, file_path)
