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

logger = logging.getLogger("sisimpur.brain.generators.qa")


class QAGenerator:
    """Generator for question-answer pairs from text content"""
    
    def __init__(self, language: str = "auto"):
        """
        Initialize the QA generator.
        
        Args:
            language: Language for generation ('auto', 'english', 'bengali')
        """
        self.language = language
        logger.info(f"Initialized QAGenerator with language: {language}")
    
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
            # Calculate optimal number of questions based on text length
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
            
            logger.info(f"Auto-generating {num_questions} questions for {word_count} words")
            return self.generate(text, num_questions)
            
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
            # Determine question type
            question_type = QUESTION_TYPE
            
            # Create appropriate prompt based on language and question type
            if self.language in ['bengali', 'bangla', 'bn']:
                prompt = self._create_bengali_prompt(text, num_questions, question_type)
            else:
                prompt = self._create_english_prompt(text, num_questions, question_type)
            
            # Generate using Gemini
            response = api.generate_content(prompt, model_name=QA_GEMINI_MODEL)
            
            # Parse response
            qa_pairs = self._parse_response(response.text, question_type)
            
            logger.info(f"Generated {len(qa_pairs)} Q&A pairs from chunk")
            return qa_pairs
            
        except Exception as e:
            logger.error(f"Error generating from chunk: {e}")
            return []
    
    def _create_english_prompt(self, text: str, num_questions: int, question_type: str) -> str:
        """Create English prompt for Q&A generation."""
        if question_type == "MULTIPLECHOICE":
            return f"""
Based on the following text, generate exactly {num_questions} multiple choice questions with {ANSWER_OPTIONS} options each.

Text:
{text}

Requirements:
1. Generate exactly {num_questions} questions
2. Each question should have {ANSWER_OPTIONS} options (A, B, C, D)
3. Clearly indicate the correct answer
4. Questions should test understanding of the content
5. Avoid questions that are too obvious or too obscure

Format your response as JSON:
{{
  "questions": [
    {{
      "question": "Question text here?",
      "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
      "answer": "Option 1",
      "correct_option": "A"
    }}
  ]
}}

Generate the questions now:
"""
        else:  # SHORT
            return f"""
Based on the following text, generate exactly {num_questions} short answer questions.

Text:
{text}

Requirements:
1. Generate exactly {num_questions} questions
2. Each question should have a concise answer (1-3 sentences)
3. Questions should test understanding of the content
4. Avoid questions that are too obvious or too obscure

Format your response as JSON:
{{
  "questions": [
    {{
      "question": "Question text here?",
      "answer": "Answer text here."
    }}
  ]
}}

Generate the questions now:
"""
    
    def _create_bengali_prompt(self, text: str, num_questions: int, question_type: str) -> str:
        """Create Bengali prompt for Q&A generation."""
        if question_type == "MULTIPLECHOICE":
            return f"""
নিচের টেক্সটের উপর ভিত্তি করে ঠিক {num_questions}টি বহুনির্বাচনী প্রশ্ন তৈরি করুন, প্রতিটিতে {ANSWER_OPTIONS}টি অপশন থাকবে।

টেক্সট:
{text}

প্রয়োজনীয়তা:
1. ঠিক {num_questions}টি প্রশ্ন তৈরি করুন
2. প্রতিটি প্রশ্নে {ANSWER_OPTIONS}টি অপশন থাকবে (ক, খ, গ, ঘ)
3. সঠিক উত্তর স্পষ্টভাবে নির্দেশ করুন
4. প্রশ্নগুলো বিষয়বস্তুর বোঝাপড়া পরীক্ষা করবে
5. খুব সহজ বা খুব কঠিন প্রশ্ন এড়িয়ে চলুন

JSON ফরম্যাটে উত্তর দিন:
{{
  "questions": [
    {{
      "question": "প্রশ্নের টেক্সট এখানে?",
      "options": ["ক) অপশন ১", "খ) অপশন ২", "গ) অপশন ৩", "ঘ) অপশন ৪"],
      "answer": "অপশন ১",
      "correct_option": "ক"
    }}
  ]
}}

এখন প্রশ্ন তৈরি করুন:
"""
        else:  # SHORT
            return f"""
নিচের টেক্সটের উপর ভিত্তি করে ঠিক {num_questions}টি সংক্ষিপ্ত উত্তরের প্রশ্ন তৈরি করুন।

টেক্সট:
{text}

প্রয়োজনীয়তা:
1. ঠিক {num_questions}টি প্রশ্ন তৈরি করুন
2. প্রতিটি প্রশ্নের সংক্ষিপ্ত উত্তর থাকবে (১-৩ বাক্য)
3. প্রশ্নগুলো বিষয়বস্তুর বোঝাপড়া পরীক্ষা করবে
4. খুব সহজ বা খুব কঠিন প্রশ্ন এড়িয়ে চলুন

JSON ফরম্যাটে উত্তর দিন:
{{
  "questions": [
    {{
      "question": "প্রশ্নের টেক্সট এখানে?",
      "answer": "উত্তরের টেক্সট এখানে।"
    }}
  ]
}}

এখন প্রশ্ন তৈরি করুন:
"""
    
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
