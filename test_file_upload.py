#!/usr/bin/env python3
"""
Test script to verify file upload and processing workflow
"""

import os
import sys
import requests
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.brain.models import ProcessingJob


def create_test_user():
    """Create a test user"""
    user, created = User.objects.get_or_create(
        username='test_upload_user',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✓ Created test user: {user.username}")
    return user


def test_file_upload_workflow():
    """Test the complete file upload workflow"""
    print("🧪 Testing File Upload Workflow")
    print("=" * 50)
    
    # Create test user
    user = create_test_user()
    
    # Create Django test client
    client = Client()
    
    # Login the user
    login_success = client.login(username='test_upload_user', password='testpass123')
    if not login_success:
        print("❌ Failed to login test user")
        return
    
    print("✓ Test user logged in")
    
    # Create a simple test file
    test_content = b"This is a test document for question generation. It contains some sample text that should be processed by the brain engine."
    test_file = SimpleUploadedFile(
        "test_document.txt",
        test_content,
        content_type="text/plain"
    )
    
    # Test the upload endpoint
    print("📤 Testing file upload...")
    
    response = client.post('/app/api/process-document/', {
        'document': test_file,
        'language': 'auto',
        'question_type': 'MULTIPLECHOICE',
        'num_questions': 3
    })
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Upload successful: {data}")
        
        if data.get('success'):
            job_id = data.get('job_id')
            print(f"✓ Job created with ID: {job_id}")
            
            # Check if job exists in database
            try:
                job = ProcessingJob.objects.get(id=job_id)
                print(f"✓ Job found in database: {job.document_name}")
                print(f"  Status: {job.status}")
                print(f"  Language: {job.language}")
                print(f"  Question Type: {job.question_type}")
                
                if job.document_file:
                    print(f"  File saved at: {job.document_file}")
                
                if job.status == 'completed':
                    qa_pairs = job.get_qa_pairs()
                    print(f"  Questions generated: {qa_pairs.count()}")
                    
                    for i, qa in enumerate(qa_pairs, 1):
                        print(f"    Q{i}: {qa.question[:50]}...")
                
            except ProcessingJob.DoesNotExist:
                print(f"❌ Job {job_id} not found in database")
        
        else:
            print(f"❌ Upload failed: {data.get('error')}")
    
    else:
        print(f"❌ Upload request failed with status {response.status_code}")
        print(f"Response: {response.content.decode()}")


def test_media_directories():
    """Test if media directories exist and are writable"""
    print("\n📁 Testing Media Directories")
    print("=" * 30)
    
    from django.conf import settings
    
    directories = [
        settings.BRAIN_UPLOADS_DIR,
        settings.BRAIN_TEMP_DIR,
        settings.BRAIN_OUTPUT_DIR
    ]
    
    for directory in directories:
        if directory.exists():
            print(f"✓ Directory exists: {directory}")
            
            # Test write permission
            test_file = directory / "test_write.txt"
            try:
                test_file.write_text("test")
                test_file.unlink()  # Delete test file
                print(f"  ✓ Write permission OK")
            except Exception as e:
                print(f"  ❌ Write permission failed: {e}")
        else:
            print(f"❌ Directory missing: {directory}")


def test_dashboard_page():
    """Test if dashboard page loads correctly"""
    print("\n🌐 Testing Dashboard Page")
    print("=" * 25)
    
    user = create_test_user()
    client = Client()
    client.login(username='test_upload_user', password='testpass123')
    
    response = client.get('/app/')
    
    if response.status_code == 200:
        print("✓ Dashboard page loads successfully")
        
        # Check if form elements are present
        content = response.content.decode()
        if 'document-upload-form' in content:
            print("✓ Upload form found")
        else:
            print("❌ Upload form not found")
            
        if 'file-input' in content:
            print("✓ File input found")
        else:
            print("❌ File input not found")
    
    else:
        print(f"❌ Dashboard page failed to load: {response.status_code}")


def main():
    """Run all tests"""
    print("🧠 Sisimpur Brain File Upload Test Suite")
    print("=" * 50)
    
    try:
        test_media_directories()
        test_dashboard_page()
        test_file_upload_workflow()
        
        print("\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
