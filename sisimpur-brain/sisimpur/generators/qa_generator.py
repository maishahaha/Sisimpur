"""
Q&A generator for Sisimpur Brain.

This module provides functionality to generate question-answer pairs from text.
"""

import json
import logging
import time
from typing import Dict, List, Any

from langchain.text_splitter import RecursiveCharacterTextSplitter

from ..utils.api_utils import api
from ..config import (
    QA_GEMINI_MODEL,
    FALLBACK_GEMINI_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    MIN_WORDS_PER_CHUNK,
    RATE_LIMIT_BATCH_SIZE,
    RATE_LIMIT_COOLDOWN,
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
    
    def generate(self, text: str, num_questions: int = 10) -> List[Dict[str, str]]:
        """
        Generate question-answer pairs from text.
        
        Args:
            text: The text to generate Q&A pairs from
            num_questions: Number of Q&A pairs to generate
            
        Returns:
            List of question-answer pairs
        """
        try:
            # Split text into chunks for processing
            chunks = self._split_text(text)
            logger.info(f"Split text into {len(chunks)} chunks")
            
            # Process chunks to generate Q&A pairs
            all_qa_pairs = []
            questions_per_chunk = max(1, num_questions // len(chunks))
            
            # Process chunks in batches with rate limiting
            for i, chunk in enumerate(chunks):
                if len(all_qa_pairs) >= num_questions:
                    break
                
                logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                
                # Apply rate limiting between batches
                if i > 0 and i % RATE_LIMIT_BATCH_SIZE == 0:
                    logger.info(f"Rate limit cooldown: sleeping for {RATE_LIMIT_COOLDOWN} seconds")
                    time.sleep(RATE_LIMIT_COOLDOWN)
                
                # Generate Q&A pairs for this chunk
                chunk_qa_pairs = self._generate_qa_for_chunk(
                    chunk, 
                    min(questions_per_chunk, num_questions - len(all_qa_pairs))
                )
                
                if chunk_qa_pairs:
                    all_qa_pairs.extend(chunk_qa_pairs)
                    logger.info(f"Generated {len(chunk_qa_pairs)} Q&A pairs from chunk {i+1}")
                else:
                    logger.warning(f"Failed to generate Q&A pairs from chunk {i+1}")
            
            # Limit to requested number of questions
            all_qa_pairs = all_qa_pairs[:num_questions]
            logger.info(f"Generated a total of {len(all_qa_pairs)} Q&A pairs")
            
            return all_qa_pairs
        
        except Exception as e:
            logger.error(f"Error generating Q&A pairs: {e}")
            raise
    
    def _split_text(self, text: str) -> List[str]:
        """
        Split text into chunks for processing.
        
        Args:
            text: The text to split
            
        Returns:
            List of text chunks
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = text_splitter.split_text(text)
        
        # Filter out chunks that are too short or contain little information
        chunks = [chunk for chunk in chunks if len(chunk.split()) > MIN_WORDS_PER_CHUNK]
        
        return chunks
    
    def _generate_qa_for_chunk(self, chunk: str, num_questions: int) -> List[Dict[str, str]]:
        """
        Generate Q&A pairs for a single chunk of text.
        
        Args:
            chunk: The text chunk
            num_questions: Number of Q&A pairs to generate
            
        Returns:
            List of question-answer pairs
        """
        # Prepare prompt based on language
        if self.language == "bengali":
            prompt_template = (
                "আমি তোমাকে একটি পাঠ্য দিচ্ছি। এই পাঠ্য থেকে {num_questions}টি প্রশ্ন ও উত্তর তৈরি করো। "
                "প্রশ্নগুলি বিভিন্ন ধরনের হতে পারে: বহুনির্বাচনী, সংক্ষিপ্ত উত্তর, বা দীর্ঘ উত্তর। "
                "প্রতিটি প্রশ্ন ও উত্তর বাংলায় লিখতে হবে। "
                "উত্তরগুলি সম্পূর্ণ ও সঠিক হতে হবে। "
                "JSON ফরম্যাটে উত্তর দাও: "
                "```json\n"
                "{{\n"
                "  \"questions\": [\n"
                "    {{\n"
                "      \"question\": \"প্রশ্ন\",\n"
                "      \"answer\": \"উত্তর\"\n"
                "    }},\n"
                "    ...\n"
                "  ]\n"
                "}}\n"
                "```\n\n"
                "পাঠ্য:\n{text}"
            )
        else:
            prompt_template = (
                "I'll provide you with a text. Generate {num_questions} question-answer pairs from this text. "
                "The questions can be of various types: multiple-choice, short answer, or long answer. "
                "Each question and answer should be in English. "
                "The answers should be comprehensive and accurate. "
                "Respond in JSON format: "
                "```json\n"
                "{{\n"
                "  \"questions\": [\n"
                "    {{\n"
                "      \"question\": \"Question\",\n"
                "      \"answer\": \"Answer\"\n"
                "    }},\n"
                "    ...\n"
                "  ]\n"
                "}}\n"
                "```\n\n"
                "Text:\n{text}"
            )
        
        # Prepare prompt for this chunk
        prompt = prompt_template.format(
            num_questions=num_questions,
            text=chunk
        )
        
        try:
            # Try with primary model first
            try:
                response = api.generate_content(prompt, model_name=QA_GEMINI_MODEL)
            except Exception as e:
                logger.warning(f"Error with primary model, trying fallback: {e}")
                response = api.generate_content(prompt, model_name=FALLBACK_GEMINI_MODEL)
            
            # Extract JSON from response
            json_str = response.text
            
            # Clean up the response to extract just the JSON part
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            qa_data = json.loads(json_str)
            
            # Validate and return Q&A pairs
            if "questions" in qa_data and isinstance(qa_data["questions"], list):
                return qa_data["questions"]
            else:
                logger.warning(f"Invalid response format: {qa_data}")
                return []
        
        except Exception as e:
            logger.error(f"Error generating Q&A pairs for chunk: {e}")
            return []
