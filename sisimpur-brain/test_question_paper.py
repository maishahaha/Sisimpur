#!/usr/bin/env python3
"""
Test script for Sisimpur Brain Question Paper Processing

This script tests the enhanced question paper processing capabilities.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path

from sisimpur.utils.document_detector import detect_document_type
from sisimpur.processor import DocumentProcessor
from sisimpur.generators.question_paper_processor import QuestionPaperProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("sisimpur.test_question_paper")

def test_question_paper_detection(file_path):
    """Test question paper detection"""
    logger.info(f"Testing question paper detection for: {file_path}")
    metadata = detect_document_type(file_path)

    if metadata.get("is_question_paper", False):
        logger.info(f"✅ Document detected as a question paper")
        logger.info(f"Language: {metadata.get('language', 'unknown')}")
    else:
        logger.info(f"❌ Document NOT detected as a question paper")

    logger.info(f"Full metadata: {metadata}")
    return metadata

def test_question_paper_processing(file_path, num_questions=None, question_type=None, num_options=None):
    """Test question paper processing"""
    if not Path(file_path).exists():
        logger.error(f"File not found: {file_path}")
        return

    # Update config if parameters are provided
    if question_type:
        from sisimpur.config import QUESTION_TYPE
        globals()["QUESTION_TYPE"] = question_type
        logger.info(f"Question type set to: {question_type}")

    if num_options:
        from sisimpur.config import ANSWER_OPTIONS
        globals()["ANSWER_OPTIONS"] = num_options
        logger.info(f"Number of options set to: {num_options}")

    logger.info(f"Processing question paper: {file_path}")
    processor = DocumentProcessor()

    try:
        output_file = processor.process(file_path, num_questions)
        logger.info(f"Q&A pairs saved to: {output_file}")

        # Display generated Q&A pairs
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        question_count = len(data["questions"])
        print(f"\n{question_count} questions extracted from question paper")
        print(f"Q&A pairs saved to: {output_file}")

        # Show a sample of questions if there are many
        sample_size = min(5, question_count)
        if sample_size > 0:
            print(f"\nShowing sample of {sample_size} questions:")
            for i, qa in enumerate(data["questions"][:sample_size], 1):
                print(f"\nQ{i}: {qa['question']}")

                # Display options if this is a multiple-choice question
                if "options" in qa:
                    print("Options:")
                    for option in qa["options"]:
                        print(f"  {option['label']}: {option['text']}")
                elif "answer" in qa:
                    print(f"A{i}: {qa['answer']}")

        return output_file

    except Exception as e:
        logger.error(f"Error processing question paper: {e}")
        return None

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Test Sisimpur Brain Question Paper Processing")
    parser.add_argument("file_path", help="Path to the question paper file")
    parser.add_argument("--questions", "-q", type=int, help="Number of Q&A pairs to extract (if not specified, will extract all)")
    parser.add_argument("--question-type", "-t", choices=["SHORT", "MULTIPLECHOICE"],
                        help="Type of questions to generate (default is set in config)")
    parser.add_argument("--options", "-o", type=int, choices=[2, 3, 4, 5, 6],
                        help="Number of options for multiple-choice questions (default is set in config)")
    parser.add_argument("--detect-only", "-d", action="store_true", help="Only detect if it's a question paper, don't process")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger("sisimpur").setLevel(logging.DEBUG)

    # Run tests
    if args.detect_only:
        test_question_paper_detection(args.file_path)
    else:
        test_question_paper_processing(
            file_path=args.file_path,
            num_questions=args.questions,
            question_type=args.question_type,
            num_options=args.options
        )

if __name__ == "__main__":
    main()
