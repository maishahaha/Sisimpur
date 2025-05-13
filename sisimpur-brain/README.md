# Sisimpur Brain

A modular document processing and Q&A generation system that can extract text from various document types and generate question-answer pairs using RAG and LLM techniques.

## Features

- **Multi-format Support**: Process PDFs, images with English/Bengali text
- **Intelligent Document Analysis**: Automatically detects document type and language
- **Specialized Extractors**: Different extraction methods for text-based PDFs, image-based PDFs, and images
- **Bengali Support**: Uses Gemini for better Bengali text recognition
- **Q&A Generation**: Creates high-quality question-answer pairs from extracted content
- **Modular Design**: Easy to extend with new document types or extraction methods

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/sisimpur.git
   cd sisimpur/sisimpur-brain
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Tesseract OCR:
   - For Ubuntu/Debian:
     ```bash
     sudo apt-get install tesseract-ocr
     sudo apt-get install tesseract-ocr-ben  # For Bengali support
     ```
   - For macOS:
     ```bash
     brew install tesseract
     brew install tesseract-lang  # Includes Bengali
     ```
   - For Windows:
     Download and install from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

4. Set up Google API key for Gemini:
   ```bash
   export GOOGLE_API_KEY="your_api_key_here"
   ```

## Usage

### Command Line Interface

Process a document and generate Q&A pairs:

```bash
python main.py path/to/your/document.pdf --questions 15
```

Options:
- `--questions` or `-q`: Number of Q&A pairs to generate (default: 10)
- `--verbose` or `-v`: Enable verbose logging

### Python API

```python
from main import DocumentProcessor

# Initialize processor
processor = DocumentProcessor()

# Process document
output_file = processor.process("path/to/document.pdf", num_questions=15)
print(f"Q&A pairs saved to: {output_file}")
```

## Output

The system generates two types of output:

1. **Extracted Text**: Saved in the `temp_extracts` directory with a timestamp
2. **Q&A Pairs**: Saved as JSON in the `qa_outputs` directory

Example JSON output:

```json
{
  "source_document": "path/to/document.pdf",
  "generated_at": "2023-06-15T14:30:45.123456",
  "questions": [
    {
      "question": "What is the main topic of the document?",
      "answer": "The document discusses artificial intelligence and its applications."
    },
    {
      "question": "When was the first AI system developed?",
      "answer": "The first AI system was developed in 1956 at Dartmouth College."
    }
  ]
}
```

## Extending the System

### Adding New Extractors

Create a new class that inherits from `BaseExtractor` and implements the `extract` method:

```python
class MyNewExtractor(BaseExtractor):
    def extract(self, file_path: str) -> str:
        # Your extraction logic here
        text = "Extracted text"
        temp_path = self.save_to_temp(text, file_path)
        return text
```

Then update the `_get_extractor` method in `DocumentProcessor` to use your new extractor.

## License

MIT
