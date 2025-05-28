"""
English context document - Short answer questions with specific count.
"""

# Metadata for this prompt
METADATA = {
    "language": "english",
    "document_type": "context_document",
    "question_type": "short",
    "count_mode": "specific",
    "description": "Specific count short answer questions for English context documents",
    "difficulty_levels": ["easy", "medium", "hard"],
    "answer_length": "1-3 sentences"
}

# The prompt template
PROMPT_TEMPLATE = """Based on the following context document, generate exactly {num_questions} short answer questions.

Context Document:
{text}

Requirements:
1. Generate exactly {num_questions} questions - no more, no less
2. Each question should have a concise answer (1-3 sentences)
3. Questions should test comprehensive understanding of the content
4. Cover different aspects and key concepts from the document
5. Avoid questions that are too obvious or too obscure
6. Ensure questions are well-distributed across the entire content
7. Include questions of varying difficulty levels if content allows
8. Focus on key facts, concepts, processes, and relationships
9. Answers should be specific and factual
10. If the content is limited, focus on the most important concepts

Format your response as JSON:
{{
  "questions": [
    {{
      "question": "Question text here?",
      "answer": "Answer text here.",
      "difficulty": "medium",
      "type": "SHORT"
    }}
  ]
}}

Generate exactly {num_questions} questions now:"""
