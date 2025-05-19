import re
import sys
from pathlib import Path

def clean_text(text: str) -> str:
    """
    Normalize into paragraphs:
     1. Strip leading/trailing whitespace
     2. Split on two-or-more newlines to get raw paragraphs
     3. Within each paragraph, collapse internal line-breaks to spaces and squash whitespace runs.
     4. Re-join paragraphs with exactly one blank line between.
    """
    text = text.strip()
    # Split into raw paragraphs
    paras = re.split(r'\n\s*\n', text)
    cleaned_paras = []
    for p in paras:
        # collapse internal line-breaks, squash whitespace
        single = ' '.join(p.splitlines())
        single = re.sub(r'\s+', ' ', single).strip()
        if single:
            cleaned_paras.append(single)
    return "\n\n".join(cleaned_paras)

def process_file(path: Path):
    # Read
    original = path.read_text(encoding='utf-8')
    # Clean
    cleaned = clean_text(original)
    # Overwrite
    path.write_text(cleaned, encoding='utf-8')
    print(f"Cleaned and updated: {path!s}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} path/to/file.txt")
        sys.exit(1)
    file_path = Path(sys.argv[1])
    if not file_path.is_file():
        print(f"Error: {file_path!s} does not exist or is not a file.")
        sys.exit(1)
    process_file(file_path)
