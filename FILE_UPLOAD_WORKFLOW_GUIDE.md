# 📁 File Upload Workflow Guide

## 🎯 Complete File Upload & Processing Workflow

The dashboard file upload system is now fully integrated with Django's file handling and the brain processing engine.

## 🔧 How It Works

### **1. File Upload Process:**
1. **User selects file** → JavaScript validates type/size
2. **Form submission** → Django receives file via `request.FILES`
3. **File validation** → Server validates file type and size
4. **File storage** → Django saves file to `media/brain/uploads/`
5. **Job creation** → ProcessingJob record created in database
6. **Processing** → Brain engine processes the document
7. **Results storage** → Q&A pairs saved to database
8. **Completion** → User redirected to results page

### **2. File Storage Structure:**
```
media/brain/
├── uploads/           # Original uploaded files
│   └── {job_id}_{filename}
├── temp_extracts/     # Extracted text files
│   └── {job_id}_extracted.txt
└── qa_outputs/        # Generated Q&A JSON files
    └── {job_id}_results.json
```

## 🧪 Testing the Workflow

### **Option 1: Django Management Command**
```bash
# Test with auto-generated content
python manage.py test_upload

# Test with specific file
python manage.py test_upload --file path/to/document.pdf
```

### **Option 2: Test Script**
```bash
# Run comprehensive test suite
python test_file_upload.py
```

### **Option 3: Web Interface**
1. Go to `http://localhost:8000/app/`
2. Upload a document (PDF, JPG, PNG)
3. Select options and click "Generate Quiz"
4. View results when processing completes

### **Option 4: CLI Tool**
```bash
# Process document via CLI
python brain_cli.py process document.pdf -n 5

# List all jobs
python brain_cli.py list
```

## 📋 Workflow Validation Checklist

### **✅ File Upload Validation:**
- [ ] File type validation (PDF, JPG, PNG only)
- [ ] File size validation (max 10MB)
- [ ] File preview with remove option
- [ ] Form validation before submission

### **✅ Django File Handling:**
- [ ] Files saved to `media/brain/uploads/`
- [ ] Unique filenames with job ID prefix
- [ ] File paths stored in database
- [ ] Proper file permissions

### **✅ Processing Pipeline:**
- [ ] ProcessingJob created with correct metadata
- [ ] Brain engine processes uploaded file
- [ ] Text extraction works (OCR for images/PDFs)
- [ ] Question generation completes
- [ ] Results saved to database

### **✅ User Experience:**
- [ ] Loading states during upload
- [ ] Success/error messages
- [ ] Redirect to results page
- [ ] Recent jobs display on dashboard

## 🔍 Debugging & Troubleshooting

### **Check File Upload:**
```python
# In Django shell
from apps.brain.models import ProcessingJob
jobs = ProcessingJob.objects.all().order_by('-created_at')
for job in jobs:
    print(f"Job {job.id}: {job.document_name} - {job.status}")
    if job.document_file:
        print(f"  File: {job.document_file}")
```

### **Check Media Directories:**
```bash
# Verify directories exist and are writable
ls -la media/brain/
ls -la media/brain/uploads/
ls -la media/brain/temp_extracts/
ls -la media/brain/qa_outputs/
```

### **Check Processing Logs:**
- Django logs show upload and processing status
- Brain engine logs show OCR and AI processing details
- Check console for JavaScript errors

### **Common Issues:**

1. **File Upload Fails:**
   - Check file permissions on media directory
   - Verify file size limits in Django settings
   - Check CSRF token in form

2. **Processing Fails:**
   - Verify brain engine dependencies installed
   - Check Gemini API key configuration
   - Review error messages in job.error_message

3. **Results Not Showing:**
   - Check if job status is 'completed'
   - Verify Q&A pairs saved to database
   - Check template rendering

## 🎯 Key Features

### **File Validation:**
- Client-side: JavaScript validates before upload
- Server-side: Django validates type, size, content
- User feedback: Clear error messages

### **Secure Storage:**
- Files stored outside web root
- Unique filenames prevent conflicts
- Proper file permissions

### **Processing Integration:**
- Seamless handoff to brain engine
- Database tracking of all jobs
- Error handling and recovery

### **User Experience:**
- Real-time upload progress
- File preview with remove option
- Immediate feedback on completion
- Easy access to results

## 🚀 Production Considerations

### **File Storage:**
- Consider using cloud storage (AWS S3, etc.)
- Implement file cleanup for old uploads
- Add virus scanning for uploaded files

### **Performance:**
- Implement background processing with Celery
- Add file compression for large uploads
- Cache frequently accessed results

### **Security:**
- Validate file content, not just extension
- Implement rate limiting for uploads
- Add user quotas and limits

---

**✅ The file upload workflow is now complete and ready for use!**

Test it using any of the methods above to ensure everything works correctly in your environment.
