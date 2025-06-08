# 🧠 Sisimpur Brain Development Guide

The brain app has been fully integrated with the dashboard. Here's how to use it for development and testing.

## 🚀 Quick Start

### 1. **Dashboard Integration**
- **Main Dashboard**: `/app/` - Shows recent quizzes and upload form
- **Quiz Generator**: `/app/quiz-generator/` - Dedicated upload page
- **My Quizzes**: `/app/my-quizzes/` - List all user's quizzes
- **Quiz Results**: `/app/quiz-results/<job_id>/` - View generated questions

### 2. **Document Processing Pipeline**
- **Upload Document** → **OCR Text Extraction** → **Question Generation** → **Results**
- Supports: PDF, JPG, PNG files
- Auto-detects: Language (English/Bengali), Question papers
- Generates: Multiple choice or short answer questions

## 🛠️ Development Tools

### **Option 1: CLI Tool (Recommended for Development)**

```bash
# Make the CLI executable
chmod +x brain_cli.py

# Process a document
python brain_cli.py process path/to/document.pdf -n 5 -l auto -t MULTIPLECHOICE

# List all jobs
python brain_cli.py list

# Show specific job results
python brain_cli.py show 1

# Quick test
python brain_cli.py test
```

**CLI Examples:**
```bash
# Process a Bengali PDF with 10 questions
python brain_cli.py process sample.pdf -n 10 -l bengali

# Process an image with short answer questions
python brain_cli.py process image.jpg -t SHORT

# Auto-detect everything
python brain_cli.py process document.pdf
```

### **Option 2: Development URLs (JSON Responses)**

**For Admin/Staff users only:**

```bash
# Test processing a file (GET request)
curl "http://localhost:8000/api/brain/dev/test/?file=/path/to/document.pdf&questions=5&language=auto&type=MULTIPLECHOICE"

# List recent jobs
curl "http://localhost:8000/api/brain/dev/jobs/"
```

**URL Parameters:**
- `file`: Path to document file (required)
- `questions`: Number of questions (default: 5)
- `language`: auto/english/bengali (default: auto)
- `type`: MULTIPLECHOICE/SHORT (default: MULTIPLECHOICE)

### **Option 3: Dashboard Web Interface**

1. **Login** to the dashboard
2. **Upload Document** via the form
3. **Monitor Progress** with real-time status updates
4. **View Results** when processing completes

## 📁 File Structure

```
apps/brain/                     # Brain app
├── models.py                   # ProcessingJob, QuestionAnswer
├── views.py                    # API endpoints + dev tools
├── urls.py                     # URL patterns
├── admin.py                    # Django admin
└── brain_engine/               # AI processing engine
    ├── processor.py            # Main document processor
    ├── extractors/             # Text extraction (OCR)
    ├── generators/             # Question generation
    └── utils/                  # Utilities

apps/dashboard/                 # Dashboard integration
├── views.py                    # Updated with brain integration
├── urls.py                     # Added brain routes
└── templates/                  # Brain-integrated templates
    ├── dashboard.html          # Main page with upload
    ├── quiz_generator.html     # Dedicated generator
    ├── my_quizzes.html         # List all quizzes
    └── quiz_results.html       # View results

brain_cli.py                    # CLI development tool
```

## 🔧 API Endpoints

### **Production Endpoints:**
- `POST /api/brain/process/document/` - Process document
- `GET /api/brain/jobs/` - List jobs
- `GET /api/brain/jobs/<id>/status/` - Job status
- `GET /api/brain/jobs/<id>/results/` - Job results
- `GET /api/brain/jobs/<id>/download/` - Download JSON

### **Development Endpoints:**
- `GET /api/brain/dev/test/` - Quick test processing
- `GET /api/brain/dev/jobs/` - List jobs (JSON)

### **Dashboard AJAX Endpoints:**
- `POST /app/api/process-document/` - Upload via dashboard
- `GET /app/api/job-status/<id>/` - Status polling

## 🧪 Testing Workflow

### **1. Quick CLI Test:**
```bash
# Test with a sample document
python brain_cli.py process sample.pdf -n 3

# Check results
python brain_cli.py list
python brain_cli.py show 1
```

### **2. Web Interface Test:**
1. Go to `http://localhost:8000/app/`
2. Upload a document
3. Watch real-time processing
4. View generated questions

### **3. API Test:**
```bash
# Direct API call
curl -X POST http://localhost:8000/api/brain/process/document/ \
  -H "Authorization: Bearer <token>" \
  -F "document=@sample.pdf" \
  -F "language=auto" \
  -F "question_type=MULTIPLECHOICE"
```

## 🎨 Features

### **Document Processing:**
- ✅ PDF text extraction
- ✅ PDF image extraction with OCR
- ✅ Image OCR (JPG, PNG)
- ✅ Bengali/English language support
- ✅ Question paper detection
- ✅ Auto question count optimization

### **Question Generation:**
- ✅ Multiple choice questions
- ✅ Short answer questions
- ✅ Confidence scoring
- ✅ Source text tracking
- ✅ Option generation for MCQs

### **Dashboard Integration:**
- ✅ File upload interface
- ✅ Real-time progress tracking
- ✅ Job management
- ✅ Results visualization
- ✅ Download functionality

## 🚨 Development Notes

### **Environment Setup:**
```bash
# Required environment variables
export GOOGLE_API_KEY="your-gemini-api-key"

# Install dependencies (LLM-based OCR, no EasyOCR needed)
pip install google-generativeai PyMuPDF pillow opencv-python-headless pdf2image
```

### **Database:**
```bash
# Run migrations
python manage.py migrate

# Create superuser for dev endpoints
python manage.py createsuperuser
```

### **File Permissions:**
- Ensure `media/brain/` directories are writable
- Check file upload size limits in Django settings

## 🎯 Quick Development Commands

```bash
# Start development server
python manage.py runserver

# Process a document via CLI
python brain_cli.py process document.pdf -n 5

# Check processing jobs
python brain_cli.py list

# View specific results
python brain_cli.py show 1

# Test via URL (admin required)
curl "http://localhost:8000/api/brain/dev/test/?file=/path/to/file.pdf&questions=3"
```

## 🔍 Debugging

### **Check Logs:**
- Django logs show processing status
- Brain engine logs show OCR/AI details
- Check `media/brain/temp_extracts/` for extracted text

### **Common Issues:**
- **Import errors**: Check if ML libraries are installed
- **OCR failures**: Verify image quality and language settings
- **API errors**: Check Gemini API key and rate limits



Use the CLI tool for quick testing, the development URLs for API testing, and the dashboard for full user experience testing.

curl "http://localhost:8000/api/brain/dev/test/?file=/path/to/file.pdf&questions=5"

python brain_cli.py process sample.pdf -n 3
python brain_cli.py list
