# -*- coding: utf-8 -*-
"""Q&A generator for SISIMPUR Brain (enhanced).

This merges the original qa_generator with enhanced mix-ins:
  • Log-scaled quota (unused, kept for backward compatibility)
  • Chunked coverage for large docs
  • Optional difficulty inference via textstat
  • Robust deduplication
  • Rich logging (INFO for high-level, DEBUG for internals)

Public API is unchanged:
  • class QAGenerator(language: str = "english")
  • generate_optimal(text: str, max_questions: Optional[int] = None) → List[Dict[str, str]]
  • generate(text: str, num_questions: int = 10, difficulty: Optional[str] = None)
    → List[Dict[str, str]]
"""

from __future__ import annotations
import json
import logging
import math
import re
from typing import Any, Dict, List, Optional, Sequence

# Optional readability scorer (Flesch–Kincaid)
try:
    import textstat  # type: ignore
except ImportError:
    textstat = None  # type: ignore

from ..utils.api_utils import api
from ..config import QA_GEMINI_MODEL, FALLBACK_GEMINI_MODEL

logger = logging.getLogger("sisimpur.generators.qa")

# ---------------------------------------------------------------------------
#  Prompt templates
# ---------------------------------------------------------------------------
_PROMPT_EN = """
You are given a passage about a specific context. Your task is to generate the *maximum possible* number of distinct, valid, askable questions from it—covering every sentence, fact, concept and section—following these strict guidelines:

1. **Exhaustive coverage**  
   • Aim to convert *every* atomic fact, definition, comparison, statistic, benefit, limitation, or process step in the passage into its own question.  
   • Include questions on biography, career, technical details, performance characteristics, underlying mechanisms, advantages, disadvantages, and all diagrams or figures described.

2. **Accuracy only**  
   • Do not invent any facts or details not present in the text.

3. **Question types**  
   • Mix question types liberally: recall (factual), comprehension/application (cause-effect, “why?”), and higher-order (analysis, evaluation, synthesis).  
   • There is no fixed percentage—choose whatever mix best covers the content.

4. **MCQs**  
   • For every MCQ: provide exactly one correct answer and three plausible but clearly wrong distractors.  
   • Distractors should be derived by slightly altering real details (e.g. swapping two numbers, negating a definition) so they’re credible yet unambiguously incorrect.  
   • Avoid quoting the passage verbatim in either the question stem or the correct answer.

5. **Descriptive questions**  
   • For any concept not suitable as an MCQ, create an open-ended question with a concise, text-based model answer.

Output only valid JSON with this schema:
[
  {{
    "question": "Your question text here",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": "Correct answer here",
    "difficulty": "easy|medium|hard",
    "type": "mcq|descriptive"
  }}
]
Do not include notes or extra keys. Output only the JSON array.

Passage:
{text}
""".strip()

_PROMPT_BN = """
আপনাকে একটি নির্দিষ্ট প্রসঙ্গ সম্পর্কে একটি অনুচ্ছেদ দেওয়া হয়েছে। আপনার কাজ হল এই কঠোর নির্দেশিকা অনুসরণ করে সর্বাধিক সংখ্যক বৈধ, জিজ্ঞাসাযোগ্য প্রশ্ন বের করা:

শুধুমাত্র সঠিকতা – অনুচ্ছেদে উপস্থিত নয় এমন তথ্য আবিষ্কার করবেন না।
ভারসাম্যপূর্ণ কভারেজ – সমস্ত প্রধান ধারণা ও বিভাগ কভার করুন।
প্রশ্নের ধরন:
  • 30% স্মরণ (তথ্যগত)
  • 40% বোধগম্যতা/প্রয়োগ (কারণ-প্রভাব, তুলনা, উদ্দেশ্য)
  • 30% উচ্চতর-ক্রম (বিশ্লেষণ, মূল্যায়ন, ব্যাখ্যা)

MCQ:
  • একটি সঠিক উত্তর
  • তিনটি সম্ভাব্য কিন্তু ভুল বিকল্প
  • অনুচ্ছেদ থেকে হুবহু উৎস নেই

বর্ণনামূলক প্রশ্নে পাঠ্য-ভিত্তিক উত্তর দিন।
ভাষা – স্পষ্ট, নিরপেক্ষ বাংলা। কোন বাগধারা নয়।

ফলস্বরূপ শুধুমাত্র এই JSON স্কিমা আউটপুট করুন:
[
  {{
    "question": "আপনার প্রশ্নের পাঠ্য এখানে",
    "options": ["ক", "খ", "গ", "ঘ"],
    "answer": "সঠিক উত্তর",
    "difficulty": "সহজ|মাঝারি|কঠিন",
    "type": "বহুনির্বাচনী|বর্ণনামূলক"
  }}
]
অতিরিক্ত কী বা নোট নেই। শুধুমাত্র JSON অ্যারে আউটপুট করুন।

অনুচ্ছেদ:
{text}
""".strip()

# ---------------------------------------------------------------------------
#  Helper utilities
# ---------------------------------------------------------------------------
def _estimate_difficulty(text: str) -> str:
    """Return 'beginner'|'intermediate'|'advanced' via Flesch–Kincaid (stub if missing)."""
    if textstat is None:
        return "intermediate"
    try:
        grade = textstat.flesch_kincaid_grade(text)
    except Exception:
        return "intermediate"
    if grade < 6:
        return "beginner"
    if grade < 10:
        return "intermediate"
    return "advanced"


def _split_into_chunks(text: str, chunk_words: int = 800, overlap: int = 80) -> List[str]:
    """Split long text into overlapping chunks for LLM calls."""
    words = text.split()
    if len(words) <= chunk_words:
        return [text]
    chunks = []
    step = chunk_words - overlap
    for i in range(0, len(words), step):
        part = words[i : i + chunk_words]
        if not part:
            break
        chunks.append(" ".join(part))
    logger.debug("Split text into %d chunks", len(chunks))
    return chunks


def _log_scaled_question_count(total_words: int, base: int = 5, cap: int = 100) -> int:
    """Logarithmically grow question count (unused, for compatibility)."""
    return max(base, min(cap, base + int(3 * math.log10(max(total_words, 1)))))


def _normalise(q: str) -> str:
    return re.sub(r"\s+", " ", q.strip().lower())


def _dedup_keep_order(items: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for qa in items:
        key = _normalise(qa.get("question", ""))
        if key and key not in seen:
            seen.add(key)
            out.append(qa)
    return out


# ---------------------------------------------------------------------------
#  Main QAGenerator class
# ---------------------------------------------------------------------------
class QAGenerator:
    """Generate question-answer pairs from free-text passages (EN & BN support)."""

    def __init__(self, language: str = "english") -> None:
        self.language = language.lower()
        self.default_difficulty: Optional[str] = None

    # ——————————————————————————————————————————————————————————————
    #  Public API
    # ——————————————————————————————————————————————————————————————
    def generate_optimal(
        self, text: str, max_questions: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Smart wrapper: uses direct LLM for small texts, chunked for large ones,
        then dedupes and applies an optional limit.
        """
        total_words = len(text.split())
        # Direct path
        if total_words < 5000:
            logger.info("Direct LLM generation for %d words", total_words)
            qas = self._call_and_parse(text)
        else:
            logger.info("Chunked LLM generation for %d words", total_words)
            chunks = _split_into_chunks(text)
            pool: List[Dict[str, str]] = []
            for idx, chunk in enumerate(chunks, 1):
                try:
                    logger.info("Processing chunk %d/%d", idx, len(chunks))
                    pool.extend(self._call_and_parse(chunk))
                except Exception as e:
                    logger.warning("Chunk %d failed: %s", idx, e)
            qas = _dedup_keep_order(pool)

        if max_questions is not None and len(qas) > max_questions:
            logger.info("Limiting to %d questions", max_questions)
            qas = qas[:max_questions]

        logger.info("Generated %d questions", len(qas))
        return qas

    def generate(
        self, text: str, num_questions: int = 10, difficulty: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Legacy-compatible entrypoint: ignores `difficulty`, calls LLM directly,
        then truncates to `num_questions`.
        """
        logger.info("Generating up to %d Q&A pairs", num_questions)
        qas = self._call_and_parse(text)
        if len(qas) > num_questions:
            logger.info("Truncating from %d to %d", len(qas), num_questions)
            qas = qas[:num_questions]
        if not qas:
            logger.warning("No Q&A pairs generated")
        else:
            logger.info("Successfully generated %d pairs", len(qas))
        return qas

    # ——————————————————————————————————————————————————————————————
    #  Internal detail methods
    # ——————————————————————————————————————————————————————————————
    def _select_prompt(self, passage: str) -> str:
        tmpl = _PROMPT_BN if self.language == "bengali" else _PROMPT_EN
        return tmpl.format(text=passage)

    def _call_model(self, prompt: str) -> Any:
        """Send prompt to primary model, fall back on error."""
        try:
            logger.debug("Calling model %s", QA_GEMINI_MODEL)
            return api.generate_content(prompt, model_name=QA_GEMINI_MODEL)
        except Exception as e:
            logger.warning("Primary model failed (%s), using fallback", e)
            return api.generate_content(prompt, model_name=FALLBACK_GEMINI_MODEL)

    @staticmethod
    def _strip_json_fence(resp_text: str) -> str:
        """Remove triple-backtick fences, returning raw JSON."""
        m = re.search(r"```json(.*?)```", resp_text, re.S) or re.search(r"```(.*?)```", resp_text, re.S)
        return m.group(1).strip() if m else resp_text

    def _parse_response(self, resp_text: str) -> List[Dict[str, str]]:
        """Parse JSON array or legacy dict structure into a list of QA dicts."""
        raw = self._strip_json_fence(resp_text)
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and isinstance(data.get("questions"), list):
            return data["questions"]
        logger.warning("Unexpected JSON format: %s", type(data))
        return []

    def _call_and_parse(self, passage: str) -> List[Dict[str, str]]:
        """Helper: build prompt, call model, and parse the JSON response."""
        prompt = self._select_prompt(passage)
        resp = self._call_model(prompt)
        try:
            return self._parse_response(resp.text)
        except json.JSONDecodeError as e:
            logger.error("JSON parsing error: %s\nRaw text: %s", e, resp.text)
            return []
        except Exception as e:
            logger.error("Error parsing response: %s", e, exc_info=True)
            return []
