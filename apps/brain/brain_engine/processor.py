"""
Main document processor for Sisimpur Brain Engine.

This module provides the main document processing pipeline.
"""

import logging
from typing import Dict, Any, Optional

from .utils.document_detector import detect_document_type
from .utils.file_utils import save_qa_pairs
from .extractors import TextPDFExtractor, ImagePDFExtractor, ImageExtractor
from .extractors.base import BaseExtractor
from .utils.extractor_factory import get_extractor

logger = logging.getLogger("sisimpur.brain.processor")


class DocumentProcessor:
    """Main document processor for the Sisimpur Brain system"""
    
    def __init__(self, language: str = "auto"):
        """
        Initialize the document processor.
        
        Args:
            language: Language for processing ('auto', 'english', 'bengali')
        """
        self.language = language
        logger.info(f"Initialized DocumentProcessor with language: {language}")
    
    def process(self, file_path: str, num_questions: Optional[int] = None) -> str:
        """
        Process a document and generate Q&A pairs.
        
        Args:
            file_path: Path to the document file
            num_questions: Number of questions to generate (optional)
            
        Returns:
            Path to the output JSON file containing Q&A pairs
        """
        try:
            logger.info(f"Starting document processing for: {file_path}")
            
            # Step 1: Detect document type and metadata
            logger.info("Detecting document type and metadata...")
            metadata = detect_document_type(file_path)
            logger.info(f"Document metadata: {metadata}")
            
            # Step 2: Determine language
            detected_language = metadata.get("language", "english")
            if self.language == "auto":
                language = detected_language
            else:
                language = self.language
            
            logger.info(f"Using language: {language}")
            
            # Step 3: Extract text using appropriate extractor
            logger.info("Extracting text from document...")
            extractor = get_extractor(metadata)
            extracted_text = extractor.extract(file_path)
            
            if not extracted_text.strip():
                raise ValueError("No text could be extracted from the document")
            
            logger.info(f"Extracted {len(extracted_text)} characters of text")
            
            # Step 4: Generate Q&A pairs
            logger.info("Generating Q&A pairs...")
            is_question_paper = metadata.get("is_question_paper", False)
            
            # Import generators here to avoid circular imports
            from .generators.qa_generator import QAGenerator
            from .generators.question_paper_processor import QuestionPaperProcessor
            
            if is_question_paper:
                # Specialized processor for genuine question papers
                logger.info("Document detected as a question paper, using specialized processor")
                processor = QuestionPaperProcessor(language=language)
                qa_pairs = processor.process(
                    extracted_text, max_questions=num_questions
                )
                logger.info(
                    f"Extracted {len(qa_pairs)} questions from question paper"
                )
            else:
                # Standard QA generation
                logger.info("Using standard QA generator")
                qa_generator = QAGenerator(language=language)
                if num_questions is None:
                    qa_pairs = qa_generator.generate_optimal(extracted_text)
                else:
                    qa_pairs = qa_generator.generate(extracted_text, num_questions)
                
                logger.info(f"Generated {len(qa_pairs)} Q&A pairs")
            
            # Step 5: Save results
            output_file = save_qa_pairs(qa_pairs, file_path)
            logger.info(f"Processing completed. Output saved to: {output_file}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            raise
    
    def process_text(self, text: str, num_questions: Optional[int] = None, 
                    source_name: str = "raw_text") -> str:
        """
        Process raw text and generate Q&A pairs.
        
        Args:
            text: Raw text to process
            num_questions: Number of questions to generate (optional)
            source_name: Name to use for the source in output
            
        Returns:
            Path to the output JSON file containing Q&A pairs
        """
        try:
            logger.info(f"Starting text processing for: {source_name}")
            
            if not text.strip():
                raise ValueError("No text provided for processing")
            
            logger.info(f"Processing {len(text)} characters of text")
            
            # Import generators here to avoid circular imports
            from .generators.qa_generator import QAGenerator
            
            # Use standard QA generation for raw text
            qa_generator = QAGenerator(language=self.language)
            if num_questions is None:
                qa_pairs = qa_generator.generate_optimal(text)
            else:
                qa_pairs = qa_generator.generate(text, num_questions)
            
            logger.info(f"Generated {len(qa_pairs)} Q&A pairs")
            
            # Save results
            output_file = save_qa_pairs(qa_pairs, source_name)
            logger.info(f"Processing completed. Output saved to: {output_file}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            raise
