import logging, numpy as np, cv2, pytesseract
from PIL import Image
from .base import BaseExtractor
from ..config import DEFAULT_GEMINI_MODEL
from ..utils_api_utils import api

logger = logging.getLogger('sisimpur.extractors.image')

class ImageExtractor(BaseExtractor):
    def extract(self, file_path:str) -> str:
        img = Image.open(file_path)
        img = self._preprocess(img)
        text = self._ocr(img)
        self.save_to_temp(text, file_path)
        return text
    
    def _preprocess(self, img: Image.Image) -> Image.Image:
        arr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        h, w = arr.shape[:2]
        