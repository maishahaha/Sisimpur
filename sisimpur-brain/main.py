#!/usr/bin/env python3
"""
Sisimpur Brain: Document Processing and Q&A Generation System

This module provides functionality to extract text from various document types
(PDF, images with English/Bengali text) and generate question-answer pairs
using RAG and LLM techniques.
"""

import os
import sys
import json
import logging
import tempfile
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

# Image processing
import cv2
import numpy as np
from PIL import Image

# PDF processing
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path

# LLM and text processing
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Create necessary directories
TEMP_DIR = Path("temp_extracts")
OUTPUT_DIR = Path("qa_outputs")
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Configure Gemini API
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GOOGLE_API_KEY not found in environment variables. Gemini features will not work.")

# Document type detection
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

            if len(text_content.strip()) > 100:  # If substantial text is extracted
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

# Text extraction modules
class BaseExtractor:
    """Base class for all document extractors"""

    def extract(self, file_path: str) -> str:
        """Extract text from document"""
        raise NotImplementedError("Subclasses must implement extract method")

    def save_to_temp(self, text: str, file_path: str) -> str:
        """Save extracted text to temporary file"""
        original_name = Path(file_path).stem
        temp_file = TEMP_DIR / f"{original_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(text)

        logger.info(f"Saved extracted text to {temp_file}")
        return str(temp_file)

class TextPDFExtractor(BaseExtractor):
    """Extractor for text-based PDF documents"""

    def extract(self, file_path: str) -> str:
        """Extract text from text-based PDF"""
        try:
            doc = fitz.open(file_path)
            text = ""

            for page_num, page in enumerate(doc):
                text += f"--- Page {page_num + 1} ---\n"
                text += page.get_text()
                text += "\n\n"

            doc.close()
            temp_path = self.save_to_temp(text, file_path)
            return text

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise

class ImagePDFExtractor(BaseExtractor):
    """Extractor for image-based PDF documents"""

    def __init__(self, language: str = "eng"):
        self.language = language

    def extract(self, file_path: str) -> str:
        """Extract text from image-based PDF using OCR"""
        try:
            # Convert PDF to images
            images = convert_from_path(file_path)
            text = ""

            for i, img in enumerate(images):
                text += f"--- Page {i + 1} ---\n"

                # Use Gemini for Bengali, pytesseract for English
                if self.language == "ben":
                    page_text = self._extract_with_gemini(img)
                else:
                    page_text = pytesseract.image_to_string(img, lang=self.language)

                text += page_text
                text += "\n\n"

            temp_path = self.save_to_temp(text, file_path)
            return text

        except Exception as e:
            logger.error(f"Error extracting text from image-based PDF: {e}")
            raise

    def _extract_with_gemini(self, img: Image.Image) -> str:
        """Extract text using Gemini for Bengali content"""
        if not GEMINI_API_KEY:
            raise ValueError("Gemini API key not configured")

        model = genai.GenerativeModel('models/gemini-1.5-flash')
        prompt = (
            "Extract all text from this image. Preserve original formatting and language. "
            "If the text is in Bengali, maintain the Bengali script. "
            "Return only the extracted text, no additional comments."
        )

        response = model.generate_content([prompt, img])
        return response.text

class ImageExtractor(BaseExtractor):
    """Extractor for image documents"""

    def __init__(self, language: str = "eng"):
        self.language = language

    def extract(self, file_path: str) -> str:
        """Extract text from image using OCR"""
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
        """Preprocess image for better OCR results"""
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
        """Extract text using Gemini for Bengali content"""
        if not GEMINI_API_KEY:
            raise ValueError("Gemini API key not configured")

        model = genai.GenerativeModel('models/gemini-1.5-flash')
        prompt = (
            "Extract all text from this image. Preserve original formatting and language. "
            "If the text is in Bengali, maintain the Bengali script. "
            "Return only the extracted text, no additional comments."
        )

        response = model.generate_content([prompt, img])
        return response.text

# Q&A Generation
class QAGenerator:
    """Generate question-answer pairs from extracted text"""

    def __init__(self, language: str = "english"):
        self.language = language

    def generate(self, text: str, num_questions: int = 10) -> List[Dict[str, str]]:
        """Generate question-answer pairs from text"""
        try:
            # Split text into chunks for processing
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            chunks = text_splitter.split_text(text)

            # Filter out chunks that are too short or contain little information
            chunks = [chunk for chunk in chunks if len(chunk.split()) > 20]

            # Use Gemini to generate Q&A pairs
            if not GEMINI_API_KEY:
                raise ValueError("Gemini API key not configured")

            model = genai.GenerativeModel('models/gemini-1.5-pro')

            # Prepare prompt based on language
            if self.language == "bengali":
                prompt_template = (
                    "আমি তোমাকে একটি পাঠ্য দিচ্ছি। এই পাঠ্য থেকে {num_questions}টি প্রশ্ন ও উত্তর তৈরি করো। "
                    "প্রশ্নগুলি বিভিন্ন ধরনের হতে পারে: বহুনির্বাচনী, সংক্ষিপ্ত উত্তর, বা দীর্ঘ উত্তর। "
                    "প্রতিটি প্রশ্ন ও উত্তর বাংলায় লিখতে হবে। "
                    "উত্তরগুলি সম্পূর্ণ ও সঠিক হতে হবে। "
                    "JSON ফরম্যাটে উত্তর দাও: "
                    "```json\n"
                    "{{\n"
                    "  \"questions\": [\n"
                    "    {{\n"
                    "      \"question\": \"প্রশ্ন\",\n"
                    "      \"answer\": \"উত্তর\"\n"
                    "    }},\n"
                    "    ...\n"
                    "  ]\n"
                    "}}\n"
                    "```\n\n"
                    "পাঠ্য:\n{text}"
                )
            else:
                prompt_template = (
                    "I'll provide you with a text. Generate {num_questions} question-answer pairs from this text. "
                    "The questions can be of various types: multiple-choice, short answer, or long answer. "
                    "Each question and answer should be in English. "
                    "The answers should be comprehensive and accurate. "
                    "Respond in JSON format: "
                    "```json\n"
                    "{{\n"
                    "  \"questions\": [\n"
                    "    {{\n"
                    "      \"question\": \"Question\",\n"
                    "      \"answer\": \"Answer\"\n"
                    "    }},\n"
                    "    ...\n"
                    "  ]\n"
                    "}}\n"
                    "```\n\n"
                    "Text:\n{text}"
                )

            # Process chunks to generate Q&A pairs
            all_qa_pairs = []
            questions_per_chunk = max(1, num_questions // len(chunks))

            for i, chunk in enumerate(chunks):
                if len(all_qa_pairs) >= num_questions:
                    break

                # Prepare prompt for this chunk
                prompt = prompt_template.format(
                    num_questions=min(questions_per_chunk, num_questions - len(all_qa_pairs)),
                    text=chunk
                )

                # Generate Q&A pairs
                response = model.generate_content(prompt)

                # Extract JSON from response
                try:
                    json_str = response.text
                    # Clean up the response to extract just the JSON part
                    if "```json" in json_str:
                        json_str = json_str.split("```json")[1].split("```")[0].strip()
                    elif "```" in json_str:
                        json_str = json_str.split("```")[1].split("```")[0].strip()

                    qa_data = json.loads(json_str)

                    # Add chunk's Q&A pairs to the overall list
                    if "questions" in qa_data and isinstance(qa_data["questions"], list):
                        all_qa_pairs.extend(qa_data["questions"])
                except Exception as e:
                    logger.error(f"Error parsing Q&A response for chunk {i}: {e}")
                    logger.debug(f"Response: {response.text}")

            # Limit to requested number of questions
            all_qa_pairs = all_qa_pairs[:num_questions]

            return all_qa_pairs

        except Exception as e:
            logger.error(f"Error generating Q&A pairs: {e}")
            raise

# Main processing pipeline
class DocumentProcessor:
    """Main document processing pipeline"""

    def process(self, file_path: str, num_questions: int = 10) -> str:
        """
        Process document and generate Q&A pairs

        Args:
            file_path: Path to the document
            num_questions: Number of Q&A pairs to generate

        Returns:
            Path to the generated JSON file
        """
        try:
            # Step 1: Detect document type
            metadata = detect_document_type(file_path)

            # Step 2: Extract text based on document type
            extractor = self._get_extractor(metadata)
            extracted_text = extractor.extract(file_path)

            # Step 3: Generate Q&A pairs
            language = metadata.get("language", "english")
            if language == "bengali":
                qa_generator = QAGenerator(language="bengali")
            else:
                qa_generator = QAGenerator(language="english")

            qa_pairs = qa_generator.generate(extracted_text, num_questions)

            # Step 4: Save Q&A pairs to JSON
            output_file = self._save_qa_pairs(qa_pairs, file_path)

            return output_file

        except Exception as e:
            logger.error(f"Error processing document: {e}")
            raise

    def _get_extractor(self, metadata: Dict[str, Any]) -> BaseExtractor:
        """Get appropriate extractor based on document metadata"""
        doc_type = metadata.get("doc_type")

        if doc_type == "pdf":
            pdf_type = metadata.get("pdf_type")
            if pdf_type == "text_based":
                return TextPDFExtractor()
            else:  # image_based or unknown
                language = metadata.get("language", "eng")
                lang_code = "ben" if language == "bengali" else "eng"
                return ImagePDFExtractor(language=lang_code)

        elif doc_type == "image":
            language = metadata.get("language", "eng")
            lang_code = "ben" if language == "bengali" else "eng"
            return ImageExtractor(language=lang_code)

        else:
            raise ValueError(f"Unsupported document type: {doc_type}")

    def _save_qa_pairs(self, qa_pairs: List[Dict[str, str]], file_path: str) -> str:
        """Save Q&A pairs to JSON file"""
        original_name = Path(file_path).stem
        output_file = OUTPUT_DIR / f"{original_name}_qa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        output_data = {
            "source_document": file_path,
            "generated_at": datetime.now().isoformat(),
            "questions": qa_pairs
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(qa_pairs)} Q&A pairs to {output_file}")
        return str(output_file)

# Command-line interface
def main():
    """Main entry point for the command-line interface"""
    parser = argparse.ArgumentParser(description="Sisimpur Brain: Document Processing and Q&A Generation")
    parser.add_argument("file_path", help="Path to the document file")
    parser.add_argument("--questions", "-q", type=int, default=10, help="Number of Q&A pairs to generate")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Process document
    try:
        processor = DocumentProcessor()
        output_file = processor.process(args.file_path, args.questions)
        print(f"Successfully processed document. Q&A pairs saved to: {output_file}")
        return 0

    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())