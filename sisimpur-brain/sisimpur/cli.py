"""
Command-line interface for Sisimpur Brain.

This module provides the command-line interface for the Sisimpur Brain system.
"""

import sys
import logging
import argparse

from .processor import DocumentProcessor
from .config import GEMINI_API_KEY

logger = logging.getLogger("sisimpur.cli")

def main():
    """Main entry point for the command-line interface"""
    parser = argparse.ArgumentParser(description="Sisimpur Brain: Document Processing and Q&A Generation")
    parser.add_argument("file_path", help="Path to the document file")
    parser.add_argument("--questions", "-q", type=int, help="Number of Q&A pairs to generate (if not specified, will auto-determine optimal count)")
    parser.add_argument("--question-type", "-t", choices=["SHORT", "MULTIPLECHOICE"],
                        help="Type of questions to generate (default is set in config)")
    parser.add_argument("--options", "-o", type=int, choices=[2, 3, 4, 5, 6],
                        help="Number of options for multiple-choice questions (default is set in config)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger("sisimpur").setLevel(logging.DEBUG)

    # Update config based on command-line arguments
    if args.question_type:
        from .config import QUESTION_TYPE
        globals()["QUESTION_TYPE"] = args.question_type
        logger.info(f"Question type set to: {args.question_type}")

    if args.options:
        from .config import ANSWER_OPTIONS
        globals()["ANSWER_OPTIONS"] = args.options
        logger.info(f"Number of options set to: {args.options}")

    # Check if API key is set
    if not GEMINI_API_KEY:
        logger.warning("GOOGLE_API_KEY not found in environment variables. Gemini features will not work.")

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
