"""
Main document processor for Sisimpur Brain.

This module provides the main document processing pipeline.
"""

import logging
from typing import Dict, Any

from .utils.document_detector import detect_document_type
from .utils.file_utils import save_qa_pairs
from .extractors import TextPDFExtractor, ImagePDFExtractor, ImageExtractor
from .extractors.base import BaseExtractor
from .generators.qa_generator import QAGenerator

logger = logging.getLogger("sisimpur.processor")

class DocumentProcessor:
    """Main document processing pipeline"""
    
    def process(self, file_path: str, num_questions: int = 10) -> str:
        """
        Process document and generate Q&A pairs.
        
        Args:
            file_path: Path to the document
            num_questions: Number of Q&A pairs to generate
            
        Returns:
            Path to the generated JSON file
        """
        try:
            # Step 1: Detect document type
            logger.info(f"Detecting document type for: {file_path}")
            metadata = detect_document_type(file_path)
            
            # Step 2: Extract text based on document type
            logger.info(f"Extracting text from document: {file_path}")
            extractor = self._get_extractor(metadata)
            extracted_text = extractor.extract(file_path)
            
            # Step 3: Generate Q&A pairs
            logger.info(f"Generating {num_questions} Q&A pairs")
            language = metadata.get("language", "english")
            if language == "bengali":
                qa_generator = QAGenerator(language="bengali")
            else:
                qa_generator = QAGenerator(language="english")
            
            qa_pairs = qa_generator.generate(extracted_text, num_questions)
            
            # Step 4: Save Q&A pairs to JSON
            output_file = save_qa_pairs(qa_pairs, file_path)
            
            return output_file
        
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            raise
    
    def _get_extractor(self, metadata: Dict[str, Any]) -> BaseExtractor:
        """
        Get appropriate extractor based on document metadata.
        
        Args:
            metadata: Document metadata
            
        Returns:
            Appropriate extractor instance
        """
        doc_type = metadata.get("doc_type")
        
        if doc_type == "pdf":
            pdf_type = metadata.get("pdf_type")
            if pdf_type == "text_based":
                logger.info("Using TextPDFExtractor")
                return TextPDFExtractor()
            else:  # image_based or unknown
                language = metadata.get("language", "eng")
                lang_code = "ben" if language == "bengali" else "eng"
                logger.info(f"Using ImagePDFExtractor with language: {lang_code}")
                return ImagePDFExtractor(language=lang_code)
        
        elif doc_type == "image":
            language = metadata.get("language", "eng")
            lang_code = "ben" if language == "bengali" else "eng"
            logger.info(f"Using ImageExtractor with language: {lang_code}")
            return ImageExtractor(language=lang_code)
        
        else:
            raise ValueError(f"Unsupported document type: {doc_type}")
