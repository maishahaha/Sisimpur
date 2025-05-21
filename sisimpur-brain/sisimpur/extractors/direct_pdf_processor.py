"""
Direct PDF processor for Sisimpur Brain.

This module provides functionality to process PDFs directly with the LLM.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from ..utils.api_utils import api
from ..config import (
    DEFAULT_GEMINI_MODEL,
    FALLBACK_GEMINI_MODEL,
    QUESTION_TYPE,
    ANSWER_OPTIONS,
)

logger = logging.getLogger("sisimpur.extractors.direct_pdf")


class DirectPDFProcessor:
    """Process PDFs directly with the LLM without extracting text or images."""

    def __init__(self, language: str = "english", is_question_paper: bool = False):
        """
        Initialize the direct PDF processor.

        Args:
            language: The language of the PDF
            is_question_paper: Whether the PDF is a question paper
        """
        self.language = language
        self.is_question_paper = is_question_paper

    def process(self, file_path: str, max_questions: Optional[int] = None) -> list:
        """
        Process a PDF directly with the LLM.

        Args:
            file_path: Path to the PDF file
            max_questions: Optional maximum number of questions to extract

        Returns:
            List of question-answer pairs or question-options pairs
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

                    prompt = (
                        f"এই PDF ফাইলটি একটি বাংলা প্রশ্নপত্র। এই প্রশ্নপত্র থেকে সবগুলো বহুনির্বাচনী প্রশ্ন নির্ণয় করো। "
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
                        "```\n"
                    )
                else:  # SHORT
                    prompt = (
                        "এই PDF ফাইলটি একটি বাংলা প্রশ্নপত্র। এই প্রশ্নপত্র থেকে সবগুলো সংক্ষিপ্ত প্রশ্ন নির্ণয় করো। "
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
                        "```\n"
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

                    prompt = (
                        "This PDF file contains a question paper. Extract all multiple-choice questions. "
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
                        "```\n"
                    )
                else:  # SHORT
                    prompt = (
                        "This PDF file contains a question paper. Extract all short-answer questions. "
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
                        "```\n"
                    )

            # Process with LLM
            try:
                logger.info("Processing PDF directly with primary model")

                # Open the PDF file
                with open(file_path, "rb") as f:
                    pdf_data = f.read()

                # Send the PDF directly to the LLM
                response = api.generate_content(
                    [prompt, pdf_data], model_name=DEFAULT_GEMINI_MODEL
                )

            except Exception as e:
                logger.warning(f"Error with primary model, trying fallback: {e}")
                logger.info("Processing PDF with fallback model")

                # Try again with fallback model
                with open(file_path, "rb") as f:
                    pdf_data = f.read()

                response = api.generate_content(
                    [prompt, pdf_data], model_name=FALLBACK_GEMINI_MODEL
                )

            # Extract JSON from response
            from ..generators.question_paper_processor import process_llm_response

            return process_llm_response(response.text, max_questions)

        except Exception as e:
            logger.error(f"Error processing PDF directly: {e}")
            return []
