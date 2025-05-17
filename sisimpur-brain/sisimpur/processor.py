"""
Main document processor for Sisimpur Brain.

This module provides the main document processing pipeline.
"""
#Need Fine tuning here
import logging
from typing import Dict, Any, Optional

from .utils.document_detector import detect_document_type
from .utils.file_utils import save_qa_pairs
from .extractors import TextPDFExtractor, ImagePDFExtractor, ImageExtractor
from .extractors.base import BaseExtractor
from .extractors.direct_pdf_processor import DirectPDFProcessor
from .generators.qa_generator import QAGenerator
from .generators.question_paper_processor import QuestionPaperProcessor
from .utils.extractor_factory import get_extractor
from .utils.file_utils import save_qa_pairs

logger = logging.getLogger("sisimpur.processor")

class DocumentProcessor:
    """Main document processing pipeline"""

    def process(self, file_path: str, num_questions: Optional[int] = None) -> str:
        """
        Process document and generate Q&A pairs.

        Args:
            file_path: Path to the document
            num_questions: Number of Q&A pairs to generate. If None, will generate
                           the maximum number of high-quality questions possible.

        Returns:
            Path to the generated JSON file
        """
        
        
        try:
            # Step 1: Detect document type
            logger.info(f"Detecting document type for: {file_path}")
            metadata = detect_document_type(file_path)

            logger.info(f"Extracting text from document: {file_path}")
            extractor = get_extractor(metadata)
            extracted_text = extractor.extract(file_path)

            # Special handling for Bengali question papers in PDF format
            language = metadata.get("language", "english")
            is_question_paper = metadata.get("is_question_paper", False)

            if (metadata.get("doc_type") == "pdf" and
                language == "bengali" and
                is_question_paper):

                # Use direct PDF processing for Bengali question papers in PDF format
                logger.info("Bengali question paper in PDF format detected - using direct PDF processing")
                direct_processor = DirectPDFProcessor(language=language, is_question_paper=True)
                qa_pairs = direct_processor.process(file_path, max_questions=num_questions)
                logger.info(f"Directly extracted {len(qa_pairs)} questions from PDF question paper")

            else:
                logger.info(f"Extracting text from document: {file_path}")
                extractor = self._get_extractor(metadata)
                extracted_text = extractor.extract(file_path)
                # Standard processing pipeline for other documents
                # Step 2: Extract text based on document type
                if is_question_paper:
                    logger.info("Document detected as a question paper, using specialized processor")
                    processor = QuestionPaperProcessor(language=language)
                    qa_pairs = processor.process(extracted_text, max_questions=num_questions)
                    logger.info(f"Extracted {len(qa_pairs)} questions from question paper")
                else:
                    logger.info("Using standard QA generator")
                    qa_generator = QAGenerator(language=language)
                    if num_questions is None:
                        logger.info("Auto-determining optimal number of questions to generate")
                        qa_pairs = qa_generator.generate_optimal(extracted_text)
                    else:
                        logger.info(f"Generating {num_questions} Q&A pairs")
                        qa_pairs = qa_generator.generate(extracted_text, num_questions)
                # Step 3: Generate Q&A pairs
                # Use specialized question paper processor if detected as a question paper
                # if is_question_paper:
                #     logger.info("Document detected as a question paper, using specialized processor")
                #     processor = QuestionPaperProcessor(language=language)
                #     qa_pairs = processor.process(extracted_text, max_questions=num_questions)
                #     logger.info(f"Extracted {len(qa_pairs)} questions from question paper")
                # else:
                #     # Use standard QA generator for regular documents
                #     logger.info("Using standard QA generator")
                #     qa_generator = QAGenerator(language=language)

                #     if num_questions is None:
                #         logger.info("Auto-determining optimal number of questions to generate")
                #         qa_pairs = qa_generator.generate_optimal(extracted_text)
                #         logger.info(f"Generated {len(qa_pairs)} questions from document")
                #     else:
                #         logger.info(f"Generating {num_questions} Q&A pairs")
                #         qa_pairs = qa_generator.generate(extracted_text, num_questions)

            # Step 4: Save Q&A pairs to JSON
            output_file = save_qa_pairs(qa_pairs, file_path)
            logger.info(f"Q&A pairs saved to {output_file}")
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
                logging.getLogger("sisimpur.processor").info("Using TextPDFExtractor")
                return TextPDFExtractor()
            else:  # image_based or unknown
                language = metadata.get("language", "eng")
                lang_code = "ben" if language == "bengali" else "eng"
                logging.getLogger("sisimpur.processor").info(f"Using ImagePDFExtractor with language: {lang_code}")
                return ImagePDFExtractor(language=lang_code)

        elif doc_type == "image":
            language = metadata.get("language", "eng")
            lang_code = "ben" if language == "bengali" else "eng"
            logging.getLogger("sisimpur.processor").info(f"Using ImageExtractor with language: {lang_code}")
            return ImageExtractor(language=lang_code)

        else:
            raise ValueError(f"Unsupported document type: {doc_type}")
