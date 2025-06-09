"""
Bengali context document - Multiple choice questions with specific count.
"""

# Metadata for this prompt
METADATA = {
    "language": "bengali",
    "document_type": "context_document",
    "question_type": "multiplechoice",
    "count_mode": "specific",
    "description": "নির্দিষ্ট সংখ্যক বহুনির্বাচনী প্রশ্ন বাংলা প্রসঙ্গ নথির জন্য",
    "difficulty_levels": ["সহজ", "মাঝারি", "কঠিন"],
    "default_options": 4
}

# The prompt template
PROMPT_TEMPLATE = """নিচের প্রসঙ্গ নথির উপর ভিত্তি করে ঠিক {num_questions}টি বহুনির্বাচনী প্রশ্ন তৈরি করুন, প্রতিটিতে {answer_options}টি অপশন থাকবে।

প্রসঙ্গ নথি:
{text}

প্রয়োজনীয়তা:
1. ঠিক {num_questions}টি প্রশ্ন তৈরি করুন - কম বা বেশি নয়
2. প্রতিটি প্রশ্নে {answer_options}টি অপশন থাকবে ({option_labels_bn})
3. সঠিক উত্তর স্পষ্টভাবে নির্দেশ করুন
4. প্রশ্নগুলো বিষয়বস্তুর সামগ্রিক বোঝাপড়া পরীক্ষা করবে
5. নথির বিভিন্ন দিক এবং মূল ধারণাগুলো অন্তর্ভুক্ত করুন
6. খুব সহজ বা খুব কঠিন প্রশ্ন এড়িয়ে চলুন
7. সম্পূর্ণ বিষয়বস্তু জুড়ে প্রশ্নগুলো সুবিতরণ নিশ্চিত করুন
8. বিষয়বস্তু অনুমতি দিলে বিভিন্ন অসুবিধার স্তরের প্রশ্ন অন্তর্ভুক্ত করুন
9. বিষয়বস্তু সীমিত হলে সবচেয়ে গুরুত্বপূর্ণ ধারণাগুলোর উপর ফোকাস করুন

JSON ফরম্যাটে উত্তর দিন:
{{
  "questions": [
    {{
      "question": "প্রশ্নের টেক্সট এখানে?",
      "options": [
        {{
          "key": "ক",
          "text": "অপশন ১"
        }},
        {{
          "key": "খ",
          "text": "অপশন ২"
        }},
        {{
          "key": "গ",
          "text": "অপশন ৩"
        }},
        {{
          "key": "ঘ",
          "text": "অপশন ৪"
        }}
      ],
      "answer": "অপশন ১",
      "correct_option": "ক",
      "difficulty": "মাঝারি",
      "type": "MULTIPLECHOICE"
    }}
  ]
}}

ঠিক {num_questions}টি প্রশ্ন তৈরি করুন:"""
