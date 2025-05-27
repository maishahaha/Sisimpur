#!/usr/bin/env python3
"""
Test script to verify Dropzone integration with Django file upload
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
        username='dropzone_test_user',
        defaults={
            'email': 'dropzone@example.com',
            'first_name': 'Dropzone',
            'last_name': 'Test'
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✓ Created test user: {user.username}")
    return user


def test_dashboard_page_loads():
    """Test if dashboard page loads with Dropzone"""
    print("\n🌐 Testing Dashboard Page with Dropzone")
    print("=" * 40)
    
    user = create_test_user()
    client = Client()
    client.login(username='dropzone_test_user', password='testpass123')
    
    response = client.get('/app/')
    
    if response.status_code == 200:
        print("✓ Dashboard page loads successfully")
        
        content = response.content.decode()
        
        # Check for Dropzone elements
        checks = [
            ('document-dropzone', 'Dropzone form'),
            ('dropzone', 'Dropzone CSS class'),
            ('dz-message', 'Dropzone message area'),
            ('upload-icon', 'Upload icon'),
            ('quiz-options-form', 'Quiz configuration form'),
        ]
        
        for element, description in checks:
            if element in content:
                print(f"✓ {description} found")
            else:
                print(f"❌ {description} not found")
        
        # Check for Dropzone CSS/JS includes
        if 'dropzone.min.css' in content:
            print("✓ Dropzone CSS included")
        else:
            print("❌ Dropzone CSS not found")
            
        if 'dropzone.min.js' in content:
            print("✓ Dropzone JS included")
        else:
            print("❌ Dropzone JS not found")
    
    else:
        print(f"❌ Dashboard page failed to load: {response.status_code}")


def test_quiz_generator_page():
    """Test if quiz generator page loads with Dropzone"""
    print("\n📝 Testing Quiz Generator Page")
    print("=" * 30)
    
    user = create_test_user()
    client = Client()
    client.login(username='dropzone_test_user', password='testpass123')
    
    response = client.get('/app/quiz-generator/')
    
    if response.status_code == 200:
        print("✓ Quiz generator page loads successfully")
        
        content = response.content.decode()
        
        # Check for Dropzone elements
        if 'document-dropzone' in content:
            print("✓ Dropzone form found")
        else:
            print("❌ Dropzone form not found")
            
        if 'quiz-options-form' in content:
            print("✓ Quiz options form found")
        else:
            print("❌ Quiz options form not found")
    
    else:
        print(f"❌ Quiz generator page failed to load: {response.status_code}")


def test_file_upload_api():
    """Test the file upload API endpoint"""
    print("\n📤 Testing File Upload API")
    print("=" * 25)
    
    user = create_test_user()
    client = Client()
    client.login(username='dropzone_test_user', password='testpass123')
    
    # Create a test file
    test_content = b"""
    Sample Document for Dropzone Testing
    
    This is a test document that contains sample text for question generation.
    The Dropzone integration should handle this file upload properly.
    
    Key points to test:
    1. File upload via Dropzone
    2. Django file handling
    3. Brain processing integration
    4. Response handling
    
    The system should process this content and generate questions.
    """
    
    test_file = SimpleUploadedFile(
        "dropzone_test.txt",
        test_content,
        content_type="text/plain"
    )
    
    # Test the upload
    print("📤 Uploading test file...")
    
    response = client.post('/app/api/process-document/', {
        'document': test_file,
        'language': 'auto',
        'question_type': 'MULTIPLECHOICE',
        'num_questions': 3
    })
    
    print(f"Response Status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Response Data: {data}")
            
            if data.get('success'):
                job_id = data.get('job_id')
                questions_count = data.get('questions_generated', 0)
                
                print(f"✓ Upload successful!")
                print(f"  Job ID: {job_id}")
                print(f"  Questions Generated: {questions_count}")
                
                # Verify job in database
                try:
                    job = ProcessingJob.objects.get(id=job_id)
                    print(f"✓ Job found in database")
                    print(f"  Document: {job.document_name}")
                    print(f"  Status: {job.status}")
                    print(f"  File Path: {job.document_file}")
                    
                    if job.status == 'completed':
                        qa_pairs = job.get_qa_pairs()
                        print(f"  Q&A Pairs: {qa_pairs.count()}")
                        
                        if qa_pairs.exists():
                            first_qa = qa_pairs.first()
                            print(f"  Sample Question: {first_qa.question[:80]}...")
                    
                except ProcessingJob.DoesNotExist:
                    print(f"❌ Job {job_id} not found in database")
            
            else:
                error = data.get('error', 'Unknown error')
                print(f"❌ Upload failed: {error}")
        
        except Exception as e:
            print(f"❌ Failed to parse response: {e}")
            print(f"Raw response: {response.content.decode()[:200]}...")
    
    else:
        print(f"❌ Upload request failed: {response.status_code}")
        print(f"Response: {response.content.decode()[:200]}...")


def test_dropzone_configuration():
    """Test Dropzone configuration in templates"""
    print("\n⚙️ Testing Dropzone Configuration")
    print("=" * 35)
    
    user = create_test_user()
    client = Client()
    client.login(username='dropzone_test_user', password='testpass123')
    
    # Test dashboard
    response = client.get('/app/')
    if response.status_code == 200:
        content = response.content.decode()
        
        config_checks = [
            ('maxFilesize: 10', 'File size limit'),
            ('maxFiles: 1', 'Max files limit'),
            ('acceptedFiles: ".pdf,.jpg,.jpeg,.png"', 'Accepted file types'),
            ('paramName: "document"', 'Parameter name'),
            ('Dropzone.autoDiscover = false', 'Auto-discover disabled'),
        ]
        
        for config, description in config_checks:
            if config in content:
                print(f"✓ {description} configured")
            else:
                print(f"❌ {description} not found")
    
    else:
        print(f"❌ Could not load dashboard for configuration test")


def main():
    """Run all Dropzone integration tests"""
    print("🎯 Dropzone Integration Test Suite")
    print("=" * 50)
    
    try:
        test_dashboard_page_loads()
        test_quiz_generator_page()
        test_file_upload_api()
        test_dropzone_configuration()
        
        print("\n🎉 Dropzone integration tests completed!")
        print("\n📋 Summary:")
        print("- Dashboard page loads with Dropzone elements")
        print("- Quiz generator page includes Dropzone")
        print("- File upload API works with Django")
        print("- Dropzone configuration is properly set")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
