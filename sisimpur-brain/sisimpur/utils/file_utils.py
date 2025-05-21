"""
File utilities for Sisimpur Brain.

This module provides utilities for file operations.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from ..config import TEMP_DIR, OUTPUT_DIR

logger = logging.getLogger("sisimpur.files")


def save_extracted_text(text: str, source_file: str) -> str:
    """
    Save extracted text to a temporary file.

    Args:
        text: The extracted text
        source_file: Path to the source file

    Returns:
        Path to the saved file
    """
    original_name = Path(source_file).stem
    temp_file = (
        TEMP_DIR / f"{original_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )

    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(text)

    logger.info(f"Saved extracted text to {temp_file}")
    return str(temp_file)


def save_qa_pairs(qa_pairs: List[Dict[str, str]], source_file: str) -> str:
    """
    Save Q&A pairs to a JSON file.

    Args:
        qa_pairs: List of question-answer pairs
        source_file: Path to the source file

    Returns:
        Path to the saved file
    """
    original_name = Path(source_file).stem
    output_file = (
        OUTPUT_DIR
        / f"{original_name}_qa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )

    output_data = {
        "source_document": source_file,
        "generated_at": datetime.now().isoformat(),
        "questions": qa_pairs,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(qa_pairs)} Q&A pairs to {output_file}")
    return str(output_file)


def load_qa_pairs(file_path: str) -> Dict[str, Any]:
    """
    Load Q&A pairs from a JSON file.

    Args:
        file_path: Path to the JSON file

    Returns:
        Dictionary containing the Q&A pairs
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data
