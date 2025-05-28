"""
Prompt Manager for Sisimpur Brain Engine.

This module manages prompt templates for different scenarios including:
- Language: English, Bengali
- Document Type: Question Paper, Context Document
- Question Type: Multiple Choice, Short Answer, Mixed
- Question Count: Auto/Optimal, Specific Number

Uses Python modules for structured prompt organization with YAML metadata.
"""

import logging
import yaml
import importlib
from pathlib import Path
from typing import Dict, Any, Optional
from ..config import QUESTION_TYPE, ANSWER_OPTIONS

logger = logging.getLogger("sisimpur.brain.prompts")


class PromptManager:
    """Manages prompt templates stored in Python modules with YAML metadata"""

    def __init__(self):
        """Initialize the prompt manager"""
        self.prompts_dir = Path(__file__).parent
        self._prompt_cache = {}
        self.config_file = self.prompts_dir / "prompts_config.yaml"
        self._load_config()
        logger.info("Initialized PromptManager with Python module prompts")

    def _load_config(self):
        """Load prompt configuration from YAML file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
            else:
                # Create default config
                self.config = self._create_default_config()
                self._save_config()
            logger.info("Loaded prompt configuration")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.config = self._create_default_config()

    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        return {
            "languages": ["english", "bengali"],
            "document_types": ["context_document", "question_paper"],
            "question_types": ["multiplechoice", "short", "mixed"],
            "count_modes": ["auto", "specific"],
            "default_answer_options": 4,
            "optimal_question_thresholds": {
                "very_short": {"max_words": 100, "questions": 2},
                "short": {"max_words": 500, "questions": 5},
                "medium": {"max_words": 1000, "questions": 8},
                "long": {"max_words": 2000, "questions": 12},
                "very_long": {"questions": 15}
            }
        }

    def _save_config(self):
        """Save configuration to YAML file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            logger.info("Saved prompt configuration")
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def get_prompt(self,
                   language: str,
                   document_type: str,
                   question_type: str,
                   question_count_mode: str,
                   text: str,
                   num_questions: Optional[int] = None,
                   answer_options: int = 4) -> str:
        """
        Get the appropriate prompt for the given parameters.

        Args:
            language: 'english' or 'bengali'
            document_type: 'question_paper' or 'context_document'
            question_type: 'MULTIPLECHOICE', 'SHORT', or 'MIXED'
            question_count_mode: 'auto' or 'specific'
            text: The source text
            num_questions: Number of questions (for specific mode)
            answer_options: Number of options for multiple choice

        Returns:
            Formatted prompt string
        """
        try:
            # Normalize parameters
            language = self._normalize_language(language)
            document_type = self._normalize_document_type(document_type)
            question_type = self._normalize_question_type(question_type)
            question_count_mode = self._normalize_count_mode(question_count_mode)

            # Get prompt from Python module
            prompt_template = self._get_prompt_from_module(
                language, document_type, question_type, question_count_mode
            )

            # Format the template with parameters
            formatted_prompt = self._format_prompt(
                prompt_template, text, num_questions, answer_options
            )

            logger.info(f"Generated prompt for: {language}/{document_type}/{question_type}/{question_count_mode}")
            return formatted_prompt

        except Exception as e:
            logger.error(f"Error generating prompt: {e}")
            # Fallback to basic prompt
            return self._get_fallback_prompt(text, num_questions or 5, question_type, language)

    def _normalize_language(self, language: str) -> str:
        """Normalize language parameter"""
        language = language.lower()
        if language in ['bengali', 'bangla', 'bn']:
            return 'bengali'
        return 'english'

    def _normalize_document_type(self, doc_type: str) -> str:
        """Normalize document type parameter"""
        if doc_type in ['question_paper', 'questionpaper', 'qp']:
            return 'question_paper'
        return 'context_document'

    def _normalize_question_type(self, q_type: str) -> str:
        """Normalize question type parameter"""
        q_type = q_type.upper()
        if q_type in ['MULTIPLECHOICE', 'MCQ', 'MC']:
            return 'multiplechoice'
        elif q_type in ['SHORT', 'SA']:
            return 'short'
        elif q_type in ['MIXED', 'MIX']:
            return 'mixed'
        return 'multiplechoice'  # default

    def _normalize_count_mode(self, mode: str) -> str:
        """Normalize question count mode"""
        if mode in ['auto', 'optimal', 'automatic']:
            return 'auto'
        return 'specific'

    def _get_prompt_from_module(self, language: str, doc_type: str,
                               q_type: str, count_mode: str) -> str:
        """Get prompt template from Python module"""
        # Create cache key
        cache_key = f"{language}_{doc_type}_{q_type}_{count_mode}"

        # Check cache first
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]

        try:
            # Import the appropriate prompt module
            module_name = f"apps.brain.brain_engine.prompts.{language}.{doc_type}.{q_type}_{count_mode}"
            module = importlib.import_module(module_name)

            # Get the prompt template
            if hasattr(module, 'PROMPT_TEMPLATE'):
                template = module.PROMPT_TEMPLATE
                self._prompt_cache[cache_key] = template
                return template
            else:
                logger.warning(f"PROMPT_TEMPLATE not found in module: {module_name}")

        except ImportError as e:
            logger.warning(f"Could not import prompt module {module_name}: {e}")
            # Try fallback to mixed template
            try:
                fallback_module = f"apps.brain.brain_engine.prompts.{language}.{doc_type}.mixed_{count_mode}"
                module = importlib.import_module(fallback_module)
                if hasattr(module, 'PROMPT_TEMPLATE'):
                    template = module.PROMPT_TEMPLATE
                    self._prompt_cache[cache_key] = template
                    return template
            except ImportError:
                pass

        except Exception as e:
            logger.error(f"Error loading prompt module: {e}")

        # Ultimate fallback
        return self._get_basic_template(language, q_type, count_mode)

    def _format_prompt(self, template: str, text: str, num_questions: Optional[int],
                      answer_options: int) -> str:
        """Format the prompt template with actual values"""
        try:
            # Calculate optimal questions if not specified
            if num_questions is None:
                word_count = len(text.split())
                if word_count < 100:
                    num_questions = 2
                elif word_count < 500:
                    num_questions = 5
                elif word_count < 1000:
                    num_questions = 8
                elif word_count < 2000:
                    num_questions = 12
                else:
                    num_questions = 15

            # Format the template
            formatted = template.format(
                text=text,
                num_questions=num_questions,
                answer_options=answer_options,
                option_labels_en="A, B, C, D" if answer_options == 4 else ", ".join([chr(65+i) for i in range(answer_options)]),
                option_labels_bn="ক, খ, গ, ঘ" if answer_options == 4 else ", ".join(["ক", "খ", "গ", "ঘ", "ঙ", "চ", "ছ", "জ"][:answer_options])
            )

            return formatted

        except Exception as e:
            logger.error(f"Error formatting prompt: {e}")
            return template  # Return unformatted template as fallback

    def _get_basic_template(self, language: str, q_type: str, count_mode: str) -> str:
        """Get a basic template as fallback"""
        if language == 'bengali':
            if q_type == 'multiplechoice':
                return """নিচের টেক্সটের উপর ভিত্তি করে ঠিক {num_questions}টি বহুনির্বাচনী প্রশ্ন তৈরি করুন।

টেক্সট:
{text}

JSON ফরম্যাটে উত্তর দিন:
{{
  "questions": [
    {{
      "question": "প্রশ্নের টেক্সট?",
      "options": ["ক) অপশন ১", "খ) অপশন ২", "গ) অপশন ৩", "ঘ) অপশন ৪"],
      "answer": "অপশন ১",
      "correct_option": "ক"
    }}
  ]
}}"""
            else:
                return """নিচের টেক্সটের উপর ভিত্তি করে ঠিক {num_questions}টি সংক্ষিপ্ত প্রশ্ন তৈরি করুন।

টেক্সট:
{text}

JSON ফরম্যাটে উত্তর দিন:
{{
  "questions": [
    {{
      "question": "প্রশ্নের টেক্সট?",
      "answer": "উত্তরের টেক্সট।"
    }}
  ]
}}"""
        else:  # English
            if q_type == 'multiplechoice':
                return """Based on the following text, generate exactly {num_questions} multiple choice questions.

Text:
{text}

Format your response as JSON:
{{
  "questions": [
    {{
      "question": "Question text?",
      "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
      "answer": "Option 1",
      "correct_option": "A"
    }}
  ]
}}"""
            else:
                return """Based on the following text, generate exactly {num_questions} short answer questions.

Text:
{text}

Format your response as JSON:
{{
  "questions": [
    {{
      "question": "Question text?",
      "answer": "Answer text."
    }}
  ]
}}"""

    def _get_fallback_prompt(self, text: str, num_questions: int,
                           question_type: str, language: str) -> str:
        """Get a simple fallback prompt"""
        template = self._get_basic_template(language, question_type.lower(), 'specific')
        return template.format(
            text=text,
            num_questions=num_questions,
            answer_options=4
        )
