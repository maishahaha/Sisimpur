# sisimpur/pipeline/extract.py
from .base import Step
from ..utils.extractor_factory import get_extractor

class ExtractStep(Step):
    """Run the appropriate extractor based on metadata."""
    def run(self, context: dict) -> dict:
        extractor = get_extractor(context['metadata'])
        context['extracted_text'] = extractor.extract(context['file_path'])
        return context