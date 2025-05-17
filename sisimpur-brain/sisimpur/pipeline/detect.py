from ..utils.document_detector import detect_document_type
from .base import Step

class DetectStep(Step):
    def run(self, context: dict) -> dict:
        metadata = detect_document_type(context['file_path'])
        context['metadata'] = metadata
        return context
