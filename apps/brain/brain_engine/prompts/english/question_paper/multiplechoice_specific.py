"""
English question paper - Multiple choice questions with specific count.
"""

# Metadata for this prompt
METADATA = {
    "language": "english",
    "document_type": "question_paper",
    "question_type": "multiplechoice",
    "count_mode": "specific",
    "description": "Specific count multiple choice questions inspired by English question papers",
    "difficulty_levels": ["easy", "medium", "hard"],
    "default_options": 4
}

# The prompt template
PROMPT_TEMPLATE = """Based on the following question paper, generate exactly {num_questions} new multiple choice questions with {answer_options} options each, inspired by the style and content of the original paper.

Original Question Paper:
{text}

Requirements:
1. Generate exactly {num_questions} questions - no more, no less
2. Each question should have {answer_options} options ({option_labels_en})
3. Maintain the same subject matter and difficulty level as the original
4. Follow the style and format of the original question paper
5. Cover similar topics and concepts as found in the original
6. Ensure questions test the same level of understanding
7. Avoid directly copying questions from the original paper
8. Create original questions that could fit in the same examination
9. If original has specific sections, distribute questions accordingly
10. Match the academic level and complexity of the original

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

Generate exactly {num_questions} questions now:"""
