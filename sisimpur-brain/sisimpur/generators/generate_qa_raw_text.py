import os
import json
import hashlib
import logging
import time
from typing import Optional

from .qa_generator import QAGenerator
from ..utils.document_detector import detect_language

logger = logging.getLogger("sisimpur.generators.generate_qa_raw_text")


def generate_qa_from_raw_text(
    text: str,
    language: str = "english",
    num_questions: Optional[int] = None,
    source_name: Optional[str] = None,
    output_dir: str = "qa_outputs",
) -> str:

    raw = language.strip().lower()
    if raw in ("auto", ""):
        lang = detect_language(text)
        logger.info(f"Auto-detected language: {lang}")
    elif raw in ("bangla", "bn"):
        lang = "bengali"
    else:
        lang = raw

    if lang not in ("english", "bengali"):
        raise ValueError(f"Unsupported language: {language}")

    os.makedirs(output_dir, exist_ok=True)

    try:
        gen = QAGenerator(language=lang)
        if num_questions is None:
            qa_pairs = gen.generate_optimal(text)
        else:
            qa_pairs = gen.generate(text, num_questions)
    except Exception as e:
        logger.error(f"Failed to generate Q&A pairs: {e}")
        qa_pairs = []

    if source_name:
        safe = (
            "".join(c for c in source_name if c.isalnum() or c in "-_").strip()[:50]
            or "raw_text"
        )
    else:
        ts = int(time.time())
        h = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
        safe = f"{ts}_{h}"

    out_path = os.path.join(output_dir, f"{safe}.json")

    payload = {"questions": qa_pairs}
    try:
        with open(out_path, "w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to write Q&A file {out_path}: {e}")
        raise

    logger.info(f"Saved Q&A to {out_path}")
    return out_path
