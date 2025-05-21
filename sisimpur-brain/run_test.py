#!/usr/bin/env python3
"""
Test script for Sisimpur Brain

This script demonstrates how to use the Sisimpur Brain system
to process documents and generate Q&A pairs.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path

from sisimpur.utils import detect_document_type
from sisimpur.processor import DocumentProcessor
from sisimpur.config import GEMINI_API_KEY

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("sisimpur.test")


def test_document_detection(file_path):
    """Test document type detection"""
    logger.info(f"Detecting document type for: {file_path}")
    metadata = detect_document_type(file_path)
    logger.info(f"Detected: {metadata}")
    return metadata


def test_document_processing(file_path, num_questions=None):
    """Test document processing and Q&A generation"""
    if not Path(file_path).exists():
        logger.error(f"File not found: {file_path}")
        return

    logger.info(f"Processing document: {file_path}")
    processor = DocumentProcessor()

    try:
        output_file = processor.process(file_path, num_questions)
        logger.info(f"Q&A pairs saved to: {output_file}")

        # Display generated Q&A pairs
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        question_count = len(data["questions"])
        print(f"\n{question_count} questions generated from document")
        print(f"Q&A pairs saved to: {output_file}")

        # Show a sample of questions if there are many
        sample_size = min(5, question_count)
        if sample_size > 0:
            print(f"\nShowing sample of {sample_size} questions:")
            for i, qa in enumerate(data["questions"][:sample_size], 1):
                print(f"\nQ{i}: {qa['question']}")
                print(f"A{i}: {qa['answer']}")

        return output_file

    except Exception as e:
        logger.error(f"Error processing document: {e}")
        return None


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Test Sisimpur Brain")
    parser.add_argument("file_path", help="Path to the document file")
    parser.add_argument(
        "--questions",
        "-q",
        type=int,
        help="Number of Q&A pairs to generate (if not specified, will auto-determine optimal count)",
    )
    parser.add_argument(
        "--detect-only",
        "-d",
        action="store_true",
        help="Only detect document type, don't process",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger("sisimpur").setLevel(logging.DEBUG)

    # Check if Google API key is set
    if not GEMINI_API_KEY:
        logger.warning(
            "GOOGLE_API_KEY not found in environment variables. Gemini features will not work."
        )
        logger.warning("Set it with: export GOOGLE_API_KEY='your_api_key_here'")

    # Run tests
    if args.detect_only:
        test_document_detection(args.file_path)
    else:
        test_document_processing(args.file_path, args.questions)


if __name__ == "__main__":
    main()
