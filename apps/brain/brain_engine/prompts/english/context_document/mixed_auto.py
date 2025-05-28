"""
English context document - Mixed questions (multiple choice + short answer) with auto count.
"""

# Metadata for this prompt
METADATA = {
    "language": "english",
    "document_type": "context_document",
    "question_type": "mixed",
    "count_mode": "auto",
    "description": "Auto mixed questions for English context documents",
    "difficulty_levels": ["easy", "medium", "hard"],
    "question_distribution": "balanced mix of multiple choice and short answer"
}

# The prompt template
PROMPT_TEMPLATE = """Based on the following context document, generate an optimal mix of multiple choice and short answer questions. The number and type distribution will be automatically determined based on the content length and complexity.

Context Document:
{text}

Requirements:
1. Generate an optimal number of questions based on content length (typically {num_questions} questions for this text)
2. Create a balanced mix of multiple choice and short answer questions
3. Multiple choice questions should have {answer_options} options ({option_labels_en})
4. Short answer questions should have concise answers (1-3 sentences)
5. Questions should test comprehensive understanding of the content
6. Cover different aspects and key concepts from the document
7. Avoid questions that are too obvious or too obscure
8. Ensure questions are well-distributed across the entire content
9. Include questions of varying difficulty levels (easy, medium, hard)
10. Use multiple choice for factual recall and short answer for deeper understanding

Format your response as JSON:
{{
  "questions": [
    {{
      "question": "Multiple choice question text here?",
      "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
      "answer": "Option 1",
      "correct_option": "A",
      "difficulty": "medium",
      "type": "MULTIPLECHOICE"
    }},
    {{
      "question": "Short answer question text here?",
      "answer": "Answer text here.",
      "difficulty": "medium",
      "type": "SHORT"
    }}
  ]
}}

Generate the mixed questions now:"""
