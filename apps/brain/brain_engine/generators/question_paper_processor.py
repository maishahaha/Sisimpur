"""
Question Paper Processor for Sisimpur Brain Engine.

This module processes existing question papers and extracts Q&A pairs.
"""

import logging
import re
from typing import List, Dict, Any, Optional

logger = logging.getLogger("sisimpur.brain.generators.question_paper")


class QuestionPaperProcessor:
    """Processor for extracting Q&A pairs from question papers"""
    
    def __init__(self, language: str = "auto"):
        """
        Initialize the question paper processor.
        
        Args:
            language: Language of the question paper ('auto', 'english', 'bengali')
        """
        self.language = language
        logger.info(f"Initialized QuestionPaperProcessor with language: {language}")
    
    def process(self, text: str, max_questions: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Process question paper text and extract Q&A pairs.
        
        Args:
            text: Question paper text
            max_questions: Maximum number of questions to extract
            
        Returns:
            List of Q&A pairs
        """
        try:
            logger.info("Processing question paper text")
            
            # Detect question type and extract questions
            if self.language in ['bengali', 'bangla', 'bn']:
                qa_pairs = self._extract_bengali_questions(text)
            else:
                qa_pairs = self._extract_english_questions(text)
            
            # Limit to max_questions if specified
            if max_questions and len(qa_pairs) > max_questions:
                qa_pairs = qa_pairs[:max_questions]
            
            logger.info(f"Extracted {len(qa_pairs)} questions from question paper")
            return qa_pairs
            
        except Exception as e:
            logger.error(f"Error processing question paper: {e}")
            raise
    
    def _extract_english_questions(self, text: str) -> List[Dict[str, Any]]:
        """Extract questions from English question paper."""
        qa_pairs = []
        
        # Pattern for numbered questions
        question_pattern = r'(\d+)\.\s*(.+?)(?=\d+\.|$)'
        matches = re.findall(question_pattern, text, re.DOTALL)
        
        for match in matches:
            question_num, question_text = match
            question_text = question_text.strip()
            
            # Check if it's multiple choice
            if self._is_multiple_choice(question_text):
                qa_pair = self._parse_mcq_english(question_text)
            else:
                qa_pair = self._parse_short_answer(question_text)
            
            if qa_pair:
                qa_pairs.append(qa_pair)
        
        return qa_pairs
    
    def _extract_bengali_questions(self, text: str) -> List[Dict[str, Any]]:
        """Extract questions from Bengali question paper."""
        qa_pairs = []
        
        # Pattern for Bengali numbered questions
        bengali_pattern = r'([১২৩৪৫৬৭৮৯০]+)\.\s*(.+?)(?=[১২৩৪৫৬৭৮৯০]+\.|$)'
        matches = re.findall(bengali_pattern, text, re.DOTALL)
        
        # Also try regular numbers
        if not matches:
            number_pattern = r'(\d+)\.\s*(.+?)(?=\d+\.|$)'
            matches = re.findall(number_pattern, text, re.DOTALL)
        
        for match in matches:
            question_num, question_text = match
            question_text = question_text.strip()
            
            # Check if it's multiple choice
            if self._is_multiple_choice_bengali(question_text):
                qa_pair = self._parse_mcq_bengali(question_text)
            else:
                qa_pair = self._parse_short_answer(question_text)
            
            if qa_pair:
                qa_pairs.append(qa_pair)
        
        return qa_pairs
    
    def _is_multiple_choice(self, text: str) -> bool:
        """Check if question is multiple choice (English)."""
        # Look for option patterns like A), B), C), D)
        option_pattern = r'[A-D]\)'
        options = re.findall(option_pattern, text)
        return len(options) >= 3
    
    def _is_multiple_choice_bengali(self, text: str) -> bool:
        """Check if question is multiple choice (Bengali)."""
        # Look for Bengali option patterns like ক), খ), গ), ঘ)
        option_pattern = r'[কখগঘ]\)'
        options = re.findall(option_pattern, text)
        return len(options) >= 3
    
    def _parse_mcq_english(self, text: str) -> Dict[str, Any]:
        """Parse English multiple choice question."""
        try:
            # Split question and options
            parts = re.split(r'[A-D]\)', text)
            question = parts[0].strip()
            
            # Extract options
            option_pattern = r'([A-D])\)\s*([^A-D\)]+?)(?=[A-D]\)|$)'
            option_matches = re.findall(option_pattern, text, re.DOTALL)
            
            options = []
            for label, option_text in option_matches:
                options.append(f"{label}) {option_text.strip()}")
            
            return {
                'question': question,
                'answer': 'Multiple choice question - answer not provided',
                'question_type': 'MULTIPLECHOICE',
                'options': options,
                'correct_option': ''  # Would need answer key to determine
            }
        except Exception as e:
            logger.error(f"Error parsing English MCQ: {e}")
            return None
    
    def _parse_mcq_bengali(self, text: str) -> Dict[str, Any]:
        """Parse Bengali multiple choice question."""
        try:
            # Split question and options
            parts = re.split(r'[কখগঘ]\)', text)
            question = parts[0].strip()
            
            # Extract options
            option_pattern = r'([কখগঘ])\)\s*([^কখগঘ\)]+?)(?=[কখগঘ]\)|$)'
            option_matches = re.findall(option_pattern, text, re.DOTALL)
            
            options = []
            for label, option_text in option_matches:
                options.append(f"{label}) {option_text.strip()}")
            
            return {
                'question': question,
                'answer': 'বহুনির্বাচনী প্রশ্ন - উত্তর প্রদান করা হয়নি',
                'question_type': 'MULTIPLECHOICE',
                'options': options,
                'correct_option': ''  # Would need answer key to determine
            }
        except Exception as e:
            logger.error(f"Error parsing Bengali MCQ: {e}")
            return None
    
    def _parse_short_answer(self, text: str) -> Dict[str, Any]:
        """Parse short answer question."""
        try:
            # For short answer questions, the entire text is usually the question
            question = text.strip()
            
            # Remove any trailing marks or instructions
            question = re.sub(r'\[\d+\s*marks?\]', '', question, flags=re.IGNORECASE)
            question = re.sub(r'\[\d+\s*নম্বর\]', '', question)
            
            return {
                'question': question,
                'answer': 'Short answer question - answer not provided',
                'question_type': 'SHORT'
            }
        except Exception as e:
            logger.error(f"Error parsing short answer: {e}")
            return None
