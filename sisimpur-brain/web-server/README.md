# Sisimpur Brain Web Server

A Flask-based web interface for the Sisimpur Brain Q&A generation system.

## Features

- Web interface for generating Q&A pairs from text
- Support for both direct text input and text file upload
- JSON API endpoint for programmatic access
- Language selection (English, Bengali, or auto-detect)
- Optional control over the number of questions to generate
- Download generated Q&A pairs as JSON

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Make sure you have set up the Sisimpur Brain module correctly with the Google API key.

## Usage

### Running the Web Server

```bash
python app.py
```

This will start the web server on http://localhost:5000.

### Using the Web Interface

1. Open your browser and navigate to http://localhost:5000
2. Enter text directly in the text area or upload a .txt file
3. Select the language (or leave as auto-detect)
4. Optionally specify the number of questions to generate
5. Click "Generate Q&A"
6. View the generated questions and download the JSON if needed

### Using the API

You can also use the API endpoint to generate Q&A pairs programmatically:

```bash
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your text content here",
    "language": "english",
    "num_questions": 5
  }'
```

## Deployment

For production deployment, it's recommended to use Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Environment Variables

- `GOOGLE_API_KEY`: Your Google API key for Gemini (required)

## Directory Structure

```
web-server/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── uploads/            # Directory for uploaded files (created automatically)
└── templates/
    └── index.html      # HTML template for the web interface
```

## API Reference

### POST /api/generate

Generate Q&A pairs from text.

**Request Body:**

```json
{
  "text": "Your text content here",
  "language": "english",  // Optional, defaults to "auto"
  "num_questions": 5      // Optional
}
```

**Response:**

```json
{
  "success": true,
  "output_file": "path/to/output.json",
  "data": {
    "questions": [
      {
        "question": "Question text",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "answer": "Option A",
        "difficulty": "medium",
        "type": "mcq"
      },
      // More questions...
    ]
  }
}
```
