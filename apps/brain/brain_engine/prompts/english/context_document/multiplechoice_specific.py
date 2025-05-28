"""
English context document - Multiple choice questions with specific count.
"""

# Metadata for this prompt
METADATA = {
    "language": "english",
    "document_type": "context_document",
    "question_type": "multiplechoice",
    "count_mode": "specific",
    "description": "Specific count multiple choice questions for English context documents",
    "difficulty_levels": ["easy", "medium", "hard"],
    "default_options": 4
}

# The prompt template
PROMPT_TEMPLATE = """Based on the following context document, generate exactly {num_questions} multiple choice questions with {answer_options} options each.

Context Document:
{text}

Requirements:
1. Generate exactly {num_questions} questions - no more, no less
2. Each question should have {answer_options} options ({option_labels_en})
3. Clearly indicate the correct answer
4. Questions should test comprehensive understanding of the content
5. Cover different aspects and key concepts from the document
6. Avoid questions that are too obvious or too obscure
7. Ensure questions are well-distributed across the entire content
8. Include questions of varying difficulty levels if content allows
9. If the content is limited, focus on the most important concepts

Format your response as JSON:
{{
  "questions": [
    {{
      "question": "Question text here?",
      "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
      "answer": "Option 1",
      "correct_option": "A",
      "difficulty": "medium",
      "type": "MULTIPLECHOICE"
    }}
  ]
}}

Generate exactly {num_questions} questions now:"""
