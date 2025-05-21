from ..extractors import TextPDFExtractor, ImagePDFExtractor, ImageExtractor
from ..extractors.base import BaseExtractor


def get_extractor(metadata: dict) -> BaseExtractor:
    """
    Selects and returns the right extractor based on metadata.
    """
    doc_type = metadata.get("doc_type")

    if doc_type == "pdf":
        pdf_type = metadata.get("pdf_type", "unknown")
        if pdf_type == "text_based":
            return TextPDFExtractor()
        else:
            # image_based or unknown
            lang = metadata.get("language", "eng")
            code = "ben" if lang == "bengali" else "eng"
            return ImagePDFExtractor(language=code)

    elif doc_type == "image":
        lang = metadata.get("language", "eng")
        code = "ben" if lang == "bengali" else "eng"
        return ImageExtractor(language=code)

    else:
        raise ValueError(f"Unsupported document type: {doc_type}")
