"""
Q&A Generator for Sisimpur Brain Engine.

This module provides functionality to generate question-answer pairs from text.
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional

from ..utils.api_utils import api
from ..config import QA_GEMINI_MODEL, QUESTION_TYPE, ANSWER_OPTIONS
from ..prompts.prompt_manager import PromptManager

logger = logging.getLogger("sisimpur.brain.generators.qa")


class QAGenerator:
    """Generator for question-answer pairs from text content"""

    def __init__(self, language: str = "auto", document_type: str = "context_document"):
        """
        Initialize the QA generator.

        Args:
            language: Language for generation ('auto', 'english', 'bengali')
            document_type: Type of document ('context_document', 'question_paper')
        """
        self.language = language
        self.document_type = document_type
        self.prompt_manager = PromptManager()
        logger.info(f"Initialized QAGenerator with language: {language}, document_type: {document_type}")

    def generate(self, text: str, num_questions: int) -> List[Dict[str, Any]]:
        """
        Generate a specific number of Q&A pairs from text.

        Args:
            text: Source text
            num_questions: Number of questions to generate

        Returns:
            List of Q&A pairs
        """
        try:
            logger.info(f"Generating {num_questions} questions from text")

            # Split text into chunks if it's too long
            chunks = self._split_text(text)

            # Distribute questions across chunks
            questions_per_chunk = max(1, num_questions // len(chunks))
            remaining_questions = num_questions % len(chunks)

            all_qa_pairs = []

            for i, chunk in enumerate(chunks):
                chunk_questions = questions_per_chunk
                if i < remaining_questions:
                    chunk_questions += 1

                if chunk_questions > 0:
                    chunk_qa_pairs = self._generate_from_chunk(chunk, chunk_questions)
                    all_qa_pairs.extend(chunk_qa_pairs)

            # Trim to exact number requested
            return all_qa_pairs[:num_questions]

        except Exception as e:
            logger.error(f"Error generating Q&A pairs: {e}")
            raise

    def generate_optimal(self, text: str) -> List[Dict[str, Any]]:
        """
        Generate optimal number of Q&A pairs based on text length.

        Args:
            text: Source text

        Returns:
            List of Q&A pairs
        """
        try:
            # Use prompt manager for optimal generation
            question_type = QUESTION_TYPE
            count_mode = "auto"  # Auto mode for optimal generation

            # Get prompt from prompt manager (it will calculate optimal questions)
            prompt = self.prompt_manager.get_prompt(
                language=self.language,
                document_type=self.document_type,
                question_type=question_type,
                question_count_mode=count_mode,
                text=text,
                num_questions=None,  # Let prompt manager calculate
                answer_options=ANSWER_OPTIONS
            )

            # Generate using Gemini
            response = api.generate_content(prompt, model_name=QA_GEMINI_MODEL)

            # Parse response
            qa_pairs = self._parse_response(response.text, question_type)

            logger.info(f"Auto-generated {len(qa_pairs)} Q&A pairs")
            return qa_pairs

        except Exception as e:
            logger.error(f"Error in optimal generation: {e}")
            raise

    def _split_text(self, text: str, max_chunk_size: int = 2000) -> List[str]:
        """Split text into manageable chunks."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0

        for word in words:
            if current_size + len(word) > max_chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
                current_size += len(word) + 1  # +1 for space

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def _generate_from_chunk(self, text: str, num_questions: int) -> List[Dict[str, Any]]:
        """Generate Q&A pairs from a text chunk."""
        try:
            # Determine question type and count mode
            question_type = QUESTION_TYPE
            count_mode = "specific"  # Since we have a specific number

            # Get prompt from prompt manager
            prompt = self.prompt_manager.get_prompt(
                language=self.language,
                document_type=self.document_type,
                question_type=question_type,
                question_count_mode=count_mode,
                text=text,
                num_questions=num_questions,
                answer_options=ANSWER_OPTIONS
            )

            # Generate using Gemini
            response = api.generate_content(prompt, model_name=QA_GEMINI_MODEL)

            # Parse response
            qa_pairs = self._parse_response(response.text, question_type)

            logger.info(f"Generated {len(qa_pairs)} Q&A pairs from chunk")
            return qa_pairs

        except Exception as e:
            logger.error(f"Error generating from chunk: {e}")
            return []

    def _parse_response(self, response_text: str, question_type: str) -> List[Dict[str, Any]]:
        """Parse the AI response and extract Q&A pairs."""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)

                if 'questions' in data:
                    qa_pairs = []
                    for item in data['questions']:
                        qa_pair = {
                            'question': item.get('question', ''),
                            'answer': item.get('answer', ''),
                            'question_type': question_type
                        }

                        if question_type == "MULTIPLECHOICE":
                            qa_pair['options'] = item.get('options', [])
                            qa_pair['correct_option'] = item.get('correct_option', '')

                        qa_pairs.append(qa_pair)

                    return qa_pairs

            # Fallback: try to parse manually
            logger.warning("Could not parse JSON response, attempting manual parsing")
            return self._manual_parse(response_text, question_type)

        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return []

    def _manual_parse(self, text: str, question_type: str) -> List[Dict[str, Any]]:
        """Manually parse response if JSON parsing fails."""
        # This is a simplified fallback parser
        # In a production system, you'd want more robust parsing
        qa_pairs = []

        # Split by question patterns
        question_patterns = [
            r'\d+\.',  # 1. 2. 3.
            r'[১২৩৪৫৬৭৮৯০]+\.',  # Bengali numbers
            r'Question \d+:',
            r'প্রশ্ন \d+:'
        ]

        for pattern in question_patterns:
            matches = re.split(pattern, text)
            if len(matches) > 1:
                for match in matches[1:]:  # Skip first empty match
                    if match.strip():
                        # Extract question and answer from the match
                        lines = match.strip().split('\n')
                        if lines:
                            question = lines[0].strip()
                            if question:
                                qa_pair = {
                                    'question': question,
                                    'answer': 'Generated answer',  # Simplified
                                    'question_type': question_type
                                }
                                qa_pairs.append(qa_pair)
                break

        return qa_pairs[:5]  # Limit to 5 questions for safety
