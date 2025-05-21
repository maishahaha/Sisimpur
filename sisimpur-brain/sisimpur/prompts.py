# sisimpur/prompts.py
def mcq_prompt(language: str, option_count: int, is_question_paper: bool) -> str:
    labels = {
        ("english", 4): "A, B, C, D",
        ("english", 5): "A, B, C, D, E",
        ("bengali", 4): "ক, খ, গ, ঘ",
        ("bengali", 5): "ক, খ, গ, ঘ, ঙ",
    }[(language, option_count)]
    if language == "english":
        base = (
            "This document contains multiple-choice questions. Each has "
            f"{option_count} options ({labels}). Extract questions + options in JSON."
        )
    else:
        base = (
            "এই ডকুমেন্টে বহুনির্বাচনী প্রশ্ন আছে। প্রতিটিতে "
            f"{option_count}টি অপশন ({labels}) আছে। JSON আকারে বের করো।"
        )
    return base


def short_prompt(language: str) -> str:
    return (
        "Extract all short-answer questions in JSON format."
        if language == "english"
        else "সব সংক্ষিপ্ত প্রশ্ন JSON আকারে বের করো।"
    )
