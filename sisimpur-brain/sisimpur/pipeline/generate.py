from .base import Step
from ..generators.qa_generator import QAGenerator
from ..generators.question_paper_processor import QuestionPaperProcessor


class GenerateQAStep(Step):
    def run(self, context: dict) -> dict:
        meta = context["metadata"]
        text = context["extracted_text"]
        num_q = context.get("num_questions")
        if meta.get("is_question_paper", False):
            qp = QuestionPaperProcessor(language=meta["language"])
            qa = qp.process(text, max_questions=num_q)
        else:
            qa_gen = QAGenerator(language=meta["language"])
            if num_q is None:
                qa = qa_gen.generate_optimal(text)
            else:
                qa = qa_gen.generate(text, num_questions=num_q)
        context["qa_pairs"] = qa
        return context
