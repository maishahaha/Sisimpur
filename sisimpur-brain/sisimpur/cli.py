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
    parser = argparse.ArgumentParser(description="Sisimpur Brain: Document Processing and Q&A Generation")
    parser.add_argument("file_path", nargs='?', help="Path to the document file")
    parser.add_argument("--questions", "-q", type=int, help="Number of Q&A pairs to generate (if not specified, will auto-determine optimal count)")
    parser.add_argument("--question-type", "-t", choices=["SHORT", "MULTIPLECHOICE"], help="Type of questions to generate (default is set in config)")
    parser.add_argument("--options", "-o", type=int, choices=[2, 3, 4, 5, 6], help="Number of options for multiple-choice questions (default is set in config)")
    parser.add_argument("--text", "-x", type=str, help="Raw passage text input or path to a .txt file to generate Q&A from")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--language", "-l", choices = ["english", "bengali", "bangla", "bn", "auto"], default="auto", help="Language for Q&A generation (english or bengali)")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger("sisimpur").setLevel(logging.DEBUG)

    if args.question_type:
        from .config import QUESTION_TYPE
        globals()["QUESTION_TYPE"] = args.question_type
        logger.info(f"Question type set to: {args.question_type}")

    if args.options:
        from .config import ANSWER_OPTIONS
        globals()["ANSWER_OPTIONS"] = args.options
        logger.info(f"Number of options set to: {args.options}")

    if not GEMINI_API_KEY:
        logger.warning("GOOGLE_API_KEY not found in environment variables. Gemini features will not work.")

    try:
        if args.text:
            from .generators.generate_qa_raw_text import generate_qa_from_raw_text
            import os.path

            # Check if the text argument is a path to a .txt file
            text_input = args.text
            source_name = None

            if args.text.lower().endswith('.txt') and os.path.isfile(args.text):
                try:
                    with open(args.text, 'r', encoding='utf-8') as file:
                        text_input = file.read()
                    logger.info(f"Successfully read text from file: {args.text}")
                    # Use the filename as the source name
                    source_name = os.path.basename(args.text)
                except Exception as e:
                    logger.error(f"Failed to read text file {args.text}: {e}")
                    print(f"Error: Could not read text file {args.text}: {e}")
                    return 1

            output_file = generate_qa_from_raw_text(
                text=text_input,
                language=args.language,
                num_questions=args.questions,
                source_name=source_name or (args.source_name if hasattr(args, "source_name") else None)
           )
            print(f"Q&A generated and saved to: {output_file}")
            return 0

        elif args.file_path:
            from .processor import DocumentProcessor

            processor = DocumentProcessor()
            output_file = processor.process(args.file_path, args.questions)
            print(f"Successfully processed document. Q&A pairs saved to: {output_file}")
            return 0

        else:
            print("Error: Provide either a file path or raw text input using --text/-x")
            return 1

    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
