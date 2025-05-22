import logging
import re
import numpy as np
import cv2
from PIL import Image
import easyocr

from .base import BaseExtractor
from ..utils.api_utils import api
from ..config import DEFAULT_GEMINI_MODEL
from ..utils.ocr_utils import ocr_with_fallback

logger = logging.getLogger("sisimpur.extractors.image")

class ImageExtractor(BaseExtractor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        lang_map = {
            "ben": "bn",
            "eng": "en",
        }
        langs = [lang_map.get(self.language, self.language)]
        self.reader = easyocr.Reader(langs, gpu=False)

    def extract(self, file_path: str) -> str:
        try:
            img = cv2.imread(file_path)
            img = self._deskew_image(img)
            text = self._extract_with_layout_ocr(img)
            self.save_to_temp(text, file_path)
            return text
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            raise

    def _deskew_image(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
        if lines is not None:
            angles = []
            for rho, theta in lines[:,0]:
                angle = (theta * 180 / np.pi) - 90
                if -45 < angle < 45:
                    angles.append(angle)
            if angles:
                median_angle = np.median(angles)
                (h, w) = img.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                img = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        return img

    def _preprocess_image(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        binary = cv2.adaptiveThreshold(gray, 255,
                                       cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV,
                                       15, 10)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9,9))
        dilated = cv2.dilate(binary, kernel, iterations=2)
        return dilated

    def _get_text_blocks(self, binary_img):
        contours, _ = cv2.findContours(binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if 150 < w < 4000 and 50 < h < 1500:
                boxes.append((x, y, w, h))
        boxes = sorted(boxes, key=lambda b: (b[1], b[0]))
        return boxes

    def _merge_close_boxes(self, boxes, max_v_gap=15, max_h_gap=15):

        if not boxes:
            return []
        merged = []
        current = boxes[0]
        for box in boxes[1:]:
            x1, y1, w1, h1 = current
            x2, y2, w2, h2 = box

            if abs(y2 - (y1 + h1)) <= max_v_gap and abs(x2 - x1) <= max_h_gap:
                new_x = min(x1, x2)
                new_y = min(y1, y2)
                new_w = max(x1 + w1, x2 + w2) - new_x
                new_h = max(y1 + h1, y2 + h2) - new_y
                current = (new_x, new_y, new_w, new_h)
            else:
                merged.append(current)
                current = box
        merged.append(current)
        return merged

    def _extract_with_layout_ocr(self, img):
        binary_img = self._preprocess_image(img)
        boxes = self._get_text_blocks(binary_img)
        boxes = self._merge_close_boxes(boxes)

        results = []
        mcq_pattern = re.compile(r'^(?:[১২৩৪৫৬৭৮৯০]+\.|\d+\.)\s*')  # Bengali/English question numbers
        option_pattern = re.compile(r'^(?:[ক-ঘ]|\([ক-ঘ]\)|[a-dA-D]|\([a-dA-D]\))[\.\)]')  # Option markers

        for (x, y, w, h) in boxes:
            crop_img = img[y:y+h, x:x+w]
            ocr_results = self.reader.readtext(crop_img, detail=1, paragraph=False)

            # Filter out low confidence results
            filtered = [res for res in ocr_results if res[2] > 0.3]

            # Group text by approximate line (using y center of box)
            lines = {}
            for bbox, text, conf in filtered:
                # bbox = 4 points, get center y
                y_center = (bbox[0][1] + bbox[2][1]) / 2
                line_key = int(y_center // 10)  # group every 10 px approx
                lines.setdefault(line_key, []).append((bbox[0][0], text))  # sort by x position later

            # Sort lines by vertical position
            sorted_lines = [lines[k] for k in sorted(lines.keys())]

            text_lines = []
            for line in sorted_lines:
                # Sort words by horizontal position
                line_sorted = sorted(line, key=lambda x: x[0])
                line_text = " ".join([w[1] for w in line_sorted])
                text_lines.append(line_text)

            # Post-process to preserve MCQ formatting
            formatted_lines = []
            for line in text_lines:
                if mcq_pattern.match(line):
                    # New question, add blank line before
                    if formatted_lines:
                        formatted_lines.append("")  
                    formatted_lines.append(line)
                elif option_pattern.match(line):
                    # Indent options
                    formatted_lines.append("    " + line)
                else:
                    # Normal continuation line
                    formatted_lines.append(line)

            block_text = "\n".join(formatted_lines)
            results.append(block_text)

        combined_text = "\n\n".join(results)
        return combined_text

    def _extract_with_gemini(self, img: Image.Image) -> str:
        """
        Extract text using Gemini for Bengali content.

        Args:
            img: The image to extract text from

        Returns:
            Extracted text
        """
        # First, try to detect if this is a question paper using a simple heuristic
        # We'll use a small portion of the image to check
        try:
            # Get a small sample of text to check if it's a question paper
            sample_text = ocr_with_fallback(img, language_code='ben')
            is_likely_question_paper = self._is_likely_question_paper(sample_text)
        except Exception:
            is_likely_question_paper = False

        # Use a specialized prompt for question papers
        if is_likely_question_paper:
            prompt = (
                "Extract all text from this question paper image with precise formatting. "
                "This appears to be an exam or question paper. "
                "Carefully preserve: "
                "1. Question numbers (including Bengali digits like ১, ২, ৩) "
                "2. All question text with exact wording "
                "3. Multiple choice options (ক, খ, গ, ঘ or A, B, C, D) "
                "4. Any instructions or headers "
                "Maintain original Bengali script and formatting. "
                "Return only the extracted text, no additional comments or analysis."
            )
        else:
            # Standard prompt for general content
            prompt = (
                "Extract all text from this image. Preserve original formatting and language. "
                "If the text is in Bengali, maintain the Bengali script. "
                "Return only the extracted text, no additional comments."
                "Generate questions from the text"
            )

        try:
            response = api.generate_content([prompt, img], model_name=DEFAULT_GEMINI_MODEL)
            return response.text
        except Exception as e:
            logger.error(f"Error using Gemini for OCR: {e}")
            # Fallback to pytesseract
            logger.info("Falling back to OCR Utils")
            return ocr_with_fallback(img, language_code='ben')

    def _is_likely_question_paper(self, text: str) -> bool:
        """
        Quick check if text is likely from a question paper.

        Args:
            text: Sample text from the image

        Returns:
            True if likely a question paper, False otherwise
        """
        # Check for Bengali question numbers
        bengali_numbers = re.findall(r'[১২৩৪৫৬৭৮৯০]+\.', text)

        # Check for Bengali MCQ options
        bengali_options = re.findall(r'[কখগঘ]\.', text)

        # Check for common Bengali question paper terms
        bengali_terms = ["প্রশ্ন", "উত্তর", "পরীক্ষা", "নম্বর"]
        term_matches = sum(1 for term in bengali_terms if term in text)

        # Check for English question numbers and options too
        question_numbers = re.findall(r'\d+\.', text)
        mcq_options = re.findall(r'[A-Da-d]\.', text)

        # If we find multiple question numbers or MCQ options
        return (len(bengali_numbers) >= 2 or
                len(bengali_options) >= 4 or
                term_matches >= 2 or
                len(question_numbers) >= 2 or
                len(mcq_options) >= 4)
