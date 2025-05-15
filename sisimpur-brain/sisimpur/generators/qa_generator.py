"""
Q&A generator for Sisimpur Brain.

This module provides functionality to generate question-answer pairs from text.
"""

import json
import logging
from typing import Dict, List, Optional

from ..utils.api_utils import api
from ..config import (
    QA_GEMINI_MODEL,
    FALLBACK_GEMINI_MODEL,
)

logger = logging.getLogger("sisimpur.generators.qa")

class QAGenerator:
    """Generate question-answer pairs from extracted text"""

    def __init__(self, language: str = "english"):
        """
        Initialize the Q&A generator.

        Args:
            language: The language to generate Q&A pairs in
        """
        self.language = language

    def generate_optimal(self, text: str, max_questions: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Generate the optimal number of high-quality question-answer pairs from text.

        This method automatically determines how many questions to generate based on
        the content and length of the text. It aims to create comprehensive coverage
        of the important concepts in the document.

        Args:
            text: The text to generate Q&A pairs from
            max_questions: Optional maximum limit on questions to generate

        Returns:
            List of question-answer pairs
        """
        try:
            # Determine optimal number of questions based on content length
            total_words = len(text.split())

            # Estimate optimal question count: roughly 1 question per 100-150 words
            # with a reasonable minimum and maximum
            optimal_total = min(max(5, total_words // 120), 100)

            if max_questions is not None:
                optimal_total = min(optimal_total, max_questions)

            logger.info(f"Determined optimal question count: {optimal_total}")

            # Generate questions using the standard method with our calculated optimal count
            return self.generate(text, optimal_total)

        except Exception as e:
            logger.error(f"Error generating optimal Q&A pairs: {e}")
            raise

    def generate(self, text: str, num_questions: int = 10) -> List[Dict[str, str]]:
        """
        Generate a specific number of question-answer pairs from text.

        Args:
            text: The text to generate Q&A pairs from
            num_questions: Number of Q&A pairs to generate

        Returns:
            List of question-answer pairs
        """
        try:
            logger.info(f"Generating {num_questions} Q&A pairs from full text")

            # Generate Q&A pairs from the entire text at once
            qa_pairs = self._generate_qa_from_text(text, num_questions)

            if qa_pairs:
                logger.info(f"Successfully generated {len(qa_pairs)} Q&A pairs")
            else:
                logger.warning("Failed to generate Q&A pairs")

            return qa_pairs

        except Exception as e:
            logger.error(f"Error generating Q&A pairs: {e}")
            raise

    def _generate_qa_from_text(self, text: str, num_questions: int) -> List[Dict[str, str]]:
        """
        Generate Q&A pairs from the entire text.

        Args:
            text: The full text to process
            num_questions: Number of Q&A pairs to generate

        Returns:
            List of question-answer pairs
        """
        # Prepare prompt based on language and configuration
        from ..config import QUESTION_TYPE, ANSWER_OPTIONS

        if self.language == "bengali":
            if QUESTION_TYPE == "MULTIPLECHOICE":
                option_count = ANSWER_OPTIONS
                option_labels = "ক, খ, গ, ঘ" if option_count == 4 else "ক, খ, গ, ঘ, ঙ" if option_count == 5 else "ক, খ, গ, ঘ, ঙ, চ"

                prompt_template = (
                    "আমি তোমাকে একটি বাংলা পাঠ্য দিচ্ছি। এই পাঠ্য থেকে {num_questions}টি বহুনির্বাচনী প্রশ্ন তৈরি করো। "
                    f"প্রতিটি প্রশ্নের {option_count}টি অপশন থাকবে ({option_labels})। "
                    "প্রতিটি প্রশ্ন ও অপশন বাংলায় লিখতে হবে। "
                    "নিম্নলিখিত JSON ফরম্যাটে উত্তর দাও: "
                    "```json\n"
                    "{{\n"
                    "  \"questions\": [\n"
                    "    {{\n"
                    "      \"question\": \"প্রশ্ন\",\n"
                    "      \"options\": [\n"
                    "        {{ \"label\": \"ক\", \"text\": \"অপশন ১\" }},\n"
                    "        {{ \"label\": \"খ\", \"text\": \"অপশন ২\" }},\n"
                    "        {{ \"label\": \"গ\", \"text\": \"অপশন ৩\" }},\n"
                    "        {{ \"label\": \"ঘ\", \"text\": \"অপশন ৪\" }}\n"
                    "      ]\n"
                    "    }},\n"
                    "    ...\n"
                    "  ]\n"
                    "}}\n"
                    "```\n\n"
                    "পাঠ্য:\n{text}"
                )
            else:  # SHORT
                prompt_template = (
                    "আমি তোমাকে একটি বাংলা পাঠ্য দিচ্ছি। এই পাঠ্য থেকে {num_questions}টি সংক্ষিপ্ত প্রশ্ন তৈরি করো। "
                    "প্রতিটি প্রশ্ন বাংলায় লিখতে হবে। "
                    "নিম্নলিখিত JSON ফরম্যাটে উত্তর দাও: "
                    "```json\n"
                    "{{\n"
                    "  \"questions\": [\n"
                    "    {{\n"
                    "      \"question\": \"প্রশ্ন\"\n"
                    "    }},\n"
                    "    ...\n"
                    "  ]\n"
                    "}}\n"
                    "```\n\n"
                    "পাঠ্য:\n{text}"
                )
        else:  # English
            if QUESTION_TYPE == "MULTIPLECHOICE":
                option_count = ANSWER_OPTIONS
                option_labels = "A, B, C, D" if option_count == 4 else "A, B, C, D, E" if option_count == 5 else "A, B, C, D, E, F"

                prompt_template = (
                    "I'll provide you with a text. Generate {num_questions} multiple-choice questions from this text. "
                    f"Each question should have {option_count} options ({option_labels}). "
                    "Each question and option should be in English. "
                    "Respond in the following JSON format: "
                    "```json\n"
                    "{{\n"
                    "  \"questions\": [\n"
                    "    {{\n"
                    "      \"question\": \"Question text\",\n"
                    "      \"options\": [\n"
                    "        {{ \"label\": \"A\", \"text\": \"Option 1\" }},\n"
                    "        {{ \"label\": \"B\", \"text\": \"Option 2\" }},\n"
                    "        {{ \"label\": \"C\", \"text\": \"Option 3\" }},\n"
                    "        {{ \"label\": \"D\", \"text\": \"Option 4\" }}\n"
                    "      ]\n"
                    "    }},\n"
                    "    ...\n"
                    "  ]\n"
                    "}}\n"
                    "```\n\n"
                    "Text:\n{text}"
                )
            else:  # SHORT
                prompt_template = (
                    "I'll provide you with a text. Generate {num_questions} short-answer questions from this text. "
                    "Each question should be in English. "
                    "Respond in the following JSON format: "
                    "```json\n"
                    "{{\n"
                    "  \"questions\": [\n"
                    "    {{\n"
                    "      \"question\": \"Question text\"\n"
                    "    }},\n"
                    "    ...\n"
                    "  ]\n"
                    "}}\n"
                    "```\n\n"
                    "Text:\n{text}"
                )

        # Prepare prompt with the full text
        prompt = prompt_template.format(
            num_questions=num_questions,
            text=text
        )

        try:
            # Try with primary model first
            try:
                logger.info("Sending request to primary model")
                response = api.generate_content(prompt, model_name=QA_GEMINI_MODEL)
            except Exception as e:
                logger.warning(f"Error with primary model, trying fallback: {e}")
                logger.info("Sending request to fallback model")
                response = api.generate_content(prompt, model_name=FALLBACK_GEMINI_MODEL)

            # Extract JSON from response
            json_str = response.text
            logger.info("Received response from model")

            # Clean up the response to extract just the JSON part
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()

            qa_data = json.loads(json_str)

            # Validate and return Q&A pairs
            if "questions" in qa_data and isinstance(qa_data["questions"], list):
                return qa_data["questions"]

            logger.warning(f"Invalid response format: {qa_data}")
            return []

        except Exception as e:
            logger.error(f"Error generating Q&A pairs from text: {e}")
            return []
