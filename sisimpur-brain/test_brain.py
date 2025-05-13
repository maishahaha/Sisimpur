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
from pathlib import Path

from main import DocumentProcessor, detect_document_type

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_document_detection():
    """Test document type detection"""
    test_files = [
        "PDF_Extractor/data/1mb.pdf",
        "PDF_Extractor/data/physics_bangla.pdf",
        "PDF_Extractor/data/1_english.jpg",
        "PDF_Extractor/data/1_bangla.jpg",
    ]
    
    for file_path in test_files:
        if not Path(file_path).exists():
            logger.warning(f"Test file not found: {file_path}")
            continue
        
        logger.info(f"Detecting document type for: {file_path}")
        metadata = detect_document_type(file_path)
        logger.info(f"Detected: {metadata}")
        print()

def test_document_processing(file_path, num_questions=3):
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
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("\nGenerated Q&A Pairs:")
        for i, qa in enumerate(data["questions"], 1):
            print(f"\nQ{i}: {qa['question']}")
            print(f"A{i}: {qa['answer']}")
    
    except Exception as e:
        logger.error(f"Error processing document: {e}")

if __name__ == "__main__":
    # Check if Google API key is set
    if not os.environ.get("GOOGLE_API_KEY"):
        logger.warning("GOOGLE_API_KEY not found in environment variables. Gemini features will not work.")
    
    # Test document detection
    print("=== Testing Document Detection ===")
    test_document_detection()
    
    # Test document processing with a sample file
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        num_questions = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        
        print(f"\n=== Testing Document Processing: {file_path} ===")
        test_document_processing(file_path, num_questions)
    else:
        logger.info("No test file provided. Usage: python test_brain.py <file_path> [num_questions]")
