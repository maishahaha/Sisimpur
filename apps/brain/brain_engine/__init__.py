"""
Sisimpur Brain Engine: Document Processing and Q&A Generation System

This package provides functionality to extract text from various document types
(PDF, images with English/Bengali text) and generate question-answer pairs
using RAG and LLM techniques.
"""

__version__ = "1.0.0"

from .processor import DocumentProcessor
from .config import BrainConfig

__all__ = [
    'DocumentProcessor',
    'BrainConfig',
]
