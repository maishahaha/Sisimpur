import logging
import fitz
from PIL import Image
from pdf2image import convert_from_path
import pytesseract
from .base import BaseExtractor
from ..config import DEFAULT_GEMINI_MODEL
from ..utils_api_utils import api

logger = logging.getLogger('sisimpur.extractors.pdf')

class TextPDFExtractor(BaseExtractor):
    def extract(self, file_path: str) -> str:
        doc = fitz.open(file_path)
        out = []
        for i, page in enumerate(doc):
            out.append(f"--- Page {i+1} ---")
            out.append(page.get_text())
        text = "\n\n".join(out)
        self.save_to_temp(text, file_path)
        return text
    
class ImagePDFExtractor(BaseExtractor):
    def extract(self, file_path: str) -> str:
        pages = convert_from_path(file_path)
        texts = []
        for i, img in enumerate(pages):
            texts.append(f"--- Page {i+1} ---")
            if self.language=='ben':
                try:
                    prompt = ("Extract the content of this image. Preserver formatting. Return text only")
                    response = api.generate.content([prompt, img], model_name = DEFAULT_GEMINI_MODEL)
                    page_text = resp.text
                except:
                    page_text = pytesseract.image_to_string(img, lang = 'ben')
            else:
                page_text = pytesseract.image_to_string(img, lang=self.language)
            
            texts.append(page_text)
        text = "\n\n".join(texts)
        self.save_to_temp(text, file_path)
        return text

            