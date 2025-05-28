"""
English context document - Short answer questions with auto count.
"""

# Metadata for this prompt
METADATA = {
    "language": "english",
    "document_type": "context_document",
    "question_type": "short",
    "count_mode": "auto",
    "description": "Auto short answer questions for English context documents",
    "difficulty_levels": ["easy", "medium", "hard"],
    "answer_length": "1-3 sentences"
}

# The prompt template
PROMPT_TEMPLATE = """Based on the following context document, generate an optimal number of short answer questions. The number of questions will be automatically determined based on the content length and complexity.

Context Document:
{text}

Requirements:
1. Generate an optimal number of questions based on content length (typically {num_questions} questions for this text)
2. Each question should have a concise answer (1-3 sentences)
3. Questions should test comprehensive understanding of the content
4. Cover different aspects and key concepts from the document
5. Avoid questions that are too obvious or too obscure
6. Ensure questions are well-distributed across the entire content
7. Include questions of varying difficulty levels (easy, medium, hard)
8. Focus on key facts, concepts, processes, and relationships
9. Answers should be specific and factual

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

Generate the questions now:"""
