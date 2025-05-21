from .base import Step
from ..utils.file_utils import save_qa_pairs


class PersistStep(Step):
    def run(self, context: dict) -> dict:
        output = save_qa_pairs(context["qa_pairs"], context["file_path"])
        context["output_file"] = output
        return context
