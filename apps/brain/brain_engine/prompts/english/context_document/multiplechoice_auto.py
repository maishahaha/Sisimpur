"""
English context document - Multiple choice questions with auto count.
"""

# Metadata for this prompt
METADATA = {
    "language": "english",
    "document_type": "context_document",
    "question_type": "multiplechoice",
    "count_mode": "auto",
    "description": "Auto multiple choice questions for English context documents",
    "difficulty_levels": ["easy", "medium", "hard"],
    "default_options": 4
}

# The prompt template
PROMPT_TEMPLATE = """Based on the following context document, generate an optimal number of multiple choice questions with {answer_options} options each. The number of questions will be automatically determined based on the content length and complexity.

Context Document:
{text}

Requirements:
1. Generate maximum optimal number of questions based on content length (typically {num_questions} questions for this text)
2. Each question should have {answer_options} options ({option_labels_en})
3. Clearly indicate the correct answer
4. Questions should test comprehensive understanding of the content
5. Cover different aspects and key concepts from the document
6. Avoid questions that are too obvious or too obscure
7. Ensure questions are well-distributed across the entire content
8. Include questions of varying difficulty levels (easy, medium, hard)

Format your response as JSON:
{{
  "questions": [
    {{
      "question": "Question text here?",
      "options": [
        {{
          "key": "A",
          "text": "Option 1"
        }},
        {{
          "key": "B",
          "text": "Option 2"
        }},
        {{
          "key": "C",
          "text": "Option 3"
        }},
        {{
          "key": "D",
          "text": "Option 4"
        }}
      ],
      "answer": "Option 1",
      "correct_option": "A",
      "difficulty": "medium",
      "type": "MULTIPLECHOICE"
    }}
  ]
}}

Generate the questions now:"""
