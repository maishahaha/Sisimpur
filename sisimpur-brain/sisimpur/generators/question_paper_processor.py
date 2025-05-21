"""
Question paper processor for Sisimpur Brain.

This module provides specialized functionality to process question papers
and extract questions and answers directly.
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any

from ..utils.api_utils import api
from ..config import (
    QA_GEMINI_MODEL,
    FALLBACK_GEMINI_MODEL,
    QUESTION_TYPE,
    ANSWER_OPTIONS,
)

logger = logging.getLogger("sisimpur.generators.question_paper")


def process_llm_response(
    json_str: str, max_questions: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Process the LLM response and extract questions.

    Args:
        json_str: JSON string from the LLM
        max_questions: Optional maximum number of questions to extract

    Returns:
        List of question-answer pairs or question-options pairs
    """
    try:
        # Clean up the response to extract just the JSON part
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        # Additional cleanup for common issues
        json_str = json_str.strip()
        if json_str.startswith("```") and json_str.endswith("```"):
            json_str = json_str[3:-3].strip()

        # Try to parse JSON
        try:
            qa_data = json.loads(json_str)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to fix common issues
            logger.warning("JSON parsing failed, attempting to fix response")

            # Try to extract anything that looks like JSON
            json_pattern = r"\{[\s\S]*\}"
            json_match = re.search(json_pattern, json_str)

            if json_match:
                json_str = json_match.group(0)
                qa_data = json.loads(json_str)
            else:
                # If we still can't find valid JSON, create a fallback structure
                logger.error("Could not extract valid JSON from response")
                qa_data = {"questions": []}

        # Validate and return Q&A pairs
        if "questions" in qa_data and isinstance(qa_data["questions"], list):
            questions = qa_data["questions"]

            # Apply max_questions limit if specified
            if max_questions is not None:
                questions = questions[:max_questions]

            # Validate each question has the required fields
            valid_questions = []
            for q in questions:
                if "question" in q:
                    # For multiple-choice questions, ensure options are properly formatted
                    if QUESTION_TYPE == "MULTIPLECHOICE" and (
                        "options" not in q or not isinstance(q["options"], list)
                    ):
                        # Try to fix missing options
                        if "options" not in q:
                            q["options"] = []
                    valid_questions.append(q)

            logger.info(f"Successfully extracted {len(valid_questions)} questions")
            return valid_questions

        logger.warning(f"Invalid response format: {qa_data}")
        return []

    except Exception as e:
        logger.error(f"Error processing model response: {e}")
        # Return empty list as fallback
        return []


class QuestionPaperProcessor:
    """Process question papers and extract questions and answers"""

    def __init__(self, language: str = "english"):
        """
        Initialize the question paper processor.

        Args:
            language: The language of the question paper
        """
        self.language = language

    def process(
        self, text: str, max_questions: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Process a question paper and extract all questions and answers.

        Args:
            text: The extracted text from the question paper
            max_questions: Optional maximum number of questions to extract

        Returns:
            List of question-answer pairs
        """
        try:
            # Prepare prompt based on language and configuration
            if self.language == "bengali":
                if QUESTION_TYPE == "MULTIPLECHOICE":
                    option_count = ANSWER_OPTIONS
                    option_labels = (
                        "ক, খ, গ, ঘ"
                        if option_count == 4
                        else (
                            "ক, খ, গ, ঘ, ঙ" if option_count == 5 else "ক, খ, গ, ঘ, ঙ, চ"
                        )
                    )

                    prompt_template = (
                        f"আমি তোমাকে একটি বাংলা প্রশ্নপত্র দিচ্ছি। এই প্রশ্নপত্র থেকে সবগুলো বহুনির্বাচনী প্রশ্ন নির্ণয় করো। "
                        f"প্রতিটি প্রশ্নের {option_count}টি অপশন আছে ({option_labels})। "
                        "প্রশ্নপত্রে থাকা প্রশ্নগুলি চিহ্নিত করো এবং প্রতিটি প্রশ্নের সমস্ত অপশন সঠিকভাবে নির্ণয় করো। "
                        "প্রতিটি প্রশ্ন ও অপশন বাংলায় লিখতে হবে। "
                        "নিম্নলিখিত JSON ফরম্যাটে উত্তর দাও: "
                        "```json\n"
                        "{\n"
                        '  "questions": [\n'
                        "    {\n"
                        '      "question": "প্রশ্ন",\n'
                        '      "options": [\n'
                        '        { "label": "ক", "text": "অপশন ১" },\n'
                        '        { "label": "খ", "text": "অপশন ২" },\n'
                        '        { "label": "গ", "text": "অপশন ৩" },\n'
                        '        { "label": "ঘ", "text": "অপশন ৪" }\n'
                        "      ]\n"
                        "    },\n"
                        "    ...\n"
                        "  ]\n"
                        "}\n"
                        "```\n\n"
                        "প্রশ্নপত্র:\n" + text
                    )
                else:  # SHORT
                    prompt_template = (
                        "আমি তোমাকে একটি বাংলা প্রশ্নপত্র দিচ্ছি। এই প্রশ্নপত্র থেকে সবগুলো সংক্ষিপ্ত প্রশ্ন নির্ণয় করো। "
                        "প্রশ্নপত্রে থাকা প্রশ্নগুলি চিহ্নিত করো। "
                        "প্রতিটি প্রশ্ন বাংলায় লিখতে হবে। "
                        "নিম্নলিখিত JSON ফরম্যাটে উত্তর দাও: "
                        "```json\n"
                        "{\n"
                        '  "questions": [\n'
                        "    {\n"
                        '      "question": "প্রশ্ন"\n'
                        "    },\n"
                        "    ...\n"
                        "  ]\n"
                        "}\n"
                        "```\n\n"
                        "প্রশ্নপত্র:\n" + text
                    )
            else:  # English
                if QUESTION_TYPE == "MULTIPLECHOICE":
                    option_count = ANSWER_OPTIONS
                    option_labels = (
                        "A, B, C, D"
                        if option_count == 4
                        else (
                            "A, B, C, D, E" if option_count == 5 else "A, B, C, D, E, F"
                        )
                    )

                    prompt_template = (
                        "I'll provide you with a question paper. Extract all multiple-choice questions. "
                        f"Each question has {option_count} options ({option_labels}). "
                        "Identify each question in the paper and extract all options accurately. "
                        "Each question and option should be in English. "
                        "Respond in the following JSON format: "
                        "```json\n"
                        "{\n"
                        '  "questions": [\n'
                        "    {\n"
                        '      "question": "Question text",\n'
                        '      "options": [\n'
                        '        { "label": "A", "text": "Option 1" },\n'
                        '        { "label": "B", "text": "Option 2" },\n'
                        '        { "label": "C", "text": "Option 3" },\n'
                        '        { "label": "D", "text": "Option 4" }\n'
                        "      ]\n"
                        "    },\n"
                        "    ...\n"
                        "  ]\n"
                        "}\n"
                        "```\n\n"
                        "Question Paper:\n" + text
                    )
                else:  # SHORT
                    prompt_template = (
                        "I'll provide you with a question paper. Extract all short-answer questions. "
                        "Identify each question in the paper. "
                        "Each question should be in English. "
                        "Respond in the following JSON format: "
                        "```json\n"
                        "{\n"
                        '  "questions": [\n'
                        "    {\n"
                        '      "question": "Question text"\n'
                        "    },\n"
                        "    ...\n"
                        "  ]\n"
                        "}\n"
                        "```\n\n"
                        "Question Paper:\n" + text
                    )

            # Process with LLM
            try:
                logger.info("Processing question paper with primary model")
                response = api.generate_content(
                    prompt_template, model_name=QA_GEMINI_MODEL
                )
            except Exception as e:
                logger.warning(f"Error with primary model, trying fallback: {e}")
                logger.info("Processing question paper with fallback model")
                response = api.generate_content(
                    prompt_template, model_name=FALLBACK_GEMINI_MODEL
                )

            # Extract JSON from response
            logger.info("Received response from model")
            return process_llm_response(response.text, max_questions)

        except Exception as e:
            logger.error(f"Error processing question paper: {e}")
            return []
