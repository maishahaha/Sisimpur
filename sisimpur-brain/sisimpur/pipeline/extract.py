from .base import Step
from ..utils.extractor_factory import get_extractor

class ExtractStep(Step):
    def run(self, context: dict) -> dict:
        extractor = get_extractor(context['metadata'])
        context['extracted_text'] = extractor.extract(context['file_path'])
        return context