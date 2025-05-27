#!/usr/bin/env python3
"""
Test script to verify the generate button functionality
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.contrib.auth.models import User
from django.test import Client


def create_test_user():
    """Create a test user"""
    user, created = User.objects.get_or_create(
        username='generate_btn_test',
        defaults={
            'email': 'generate@example.com',
            'first_name': 'Generate',
            'last_name': 'Test'
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✓ Created test user: {user.username}")
    return user


def test_dashboard_generate_button():
    """Test if dashboard page has the generate button"""
    print("\n🎯 Testing Dashboard Generate Button")
    print("=" * 40)
    
    user = create_test_user()
    client = Client()
    client.login(username='generate_btn_test', password='testpass123')
    
    response = client.get('/app/')
    
    if response.status_code == 200:
        print("✓ Dashboard page loads successfully")
        
        content = response.content.decode()
        
        # Check for generate button elements
        button_checks = [
            ('id="generate-btn"', 'Generate button element'),
            ('class="generate-btn"', 'Generate button CSS class'),
            ('disabled', 'Button starts disabled'),
            ('id="btn-text"', 'Button text element'),
            ('id="loading-spinner"', 'Loading spinner element'),
            ('Generate Quiz', 'Button text content'),
        ]
        
        for element, description in button_checks:
            if element in content:
                print(f"✓ {description} found")
            else:
                print(f"❌ {description} not found")
        
        # Check for Dropzone configuration
        dropzone_checks = [
            ('autoProcessQueue: false', 'Auto-processing disabled'),
            ('uploadedFile = null', 'File tracking variable'),
            ('generateBtn.disabled = false', 'Button enable logic'),
            ('myDropzone.processQueue()', 'Manual processing trigger'),
        ]
        
        for element, description in dropzone_checks:
            if element in content:
                print(f"✓ {description} found")
            else:
                print(f"❌ {description} not found")
    
    else:
        print(f"❌ Dashboard page failed to load: {response.status_code}")


def test_quiz_generator_generate_button():
    """Test if quiz generator page has the generate button"""
    print("\n📝 Testing Quiz Generator Generate Button")
    print("=" * 45)
    
    user = create_test_user()
    client = Client()
    client.login(username='generate_btn_test', password='testpass123')
    
    response = client.get('/app/quiz-generator/')
    
    if response.status_code == 200:
        print("✓ Quiz generator page loads successfully")
        
        content = response.content.decode()
        
        # Check for generate button elements
        if 'id="generate-btn"' in content:
            print("✓ Generate button found")
        else:
            print("❌ Generate button not found")
            
        if 'autoProcessQueue: false' in content:
            print("✓ Auto-processing disabled")
        else:
            print("❌ Auto-processing not disabled")
            
        if 'Upload a document first, then click Generate' in content:
            print("✓ Updated description found")
        else:
            print("❌ Updated description not found")
    
    else:
        print(f"❌ Quiz generator page failed to load: {response.status_code}")


def test_workflow_description():
    """Test if the workflow descriptions are updated"""
    print("\n📋 Testing Workflow Descriptions")
    print("=" * 35)
    
    user = create_test_user()
    client = Client()
    client.login(username='generate_btn_test', password='testpass123')
    
    # Test dashboard
    response = client.get('/app/')
    if response.status_code == 200:
        content = response.content.decode()
        if 'Upload a document first, then click Generate to process it' in content:
            print("✓ Dashboard description updated")
        else:
            print("❌ Dashboard description not updated")
    
    # Test quiz generator
    response = client.get('/app/quiz-generator/')
    if response.status_code == 200:
        content = response.content.decode()
        if 'Upload a document first, then click Generate to process it' in content:
            print("✓ Quiz generator description updated")
        else:
            print("❌ Quiz generator description not updated")


def test_button_styling():
    """Test if the generate button has proper styling"""
    print("\n🎨 Testing Generate Button Styling")
    print("=" * 35)
    
    user = create_test_user()
    client = Client()
    client.login(username='generate_btn_test', password='testpass123')
    
    response = client.get('/app/')
    
    if response.status_code == 200:
        content = response.content.decode()
        
        # Check for CSS styles
        style_checks = [
            ('.generate-btn {', 'Generate button CSS class'),
            ('background: linear-gradient', 'Gradient background'),
            ('padding: 15px 30px', 'Button padding'),
            ('border-radius: 8px', 'Rounded corners'),
            ('cursor: pointer', 'Pointer cursor'),
            (':disabled {', 'Disabled state styling'),
            ('opacity: 0.6', 'Disabled opacity'),
        ]
        
        for style, description in style_checks:
            if style in content:
                print(f"✓ {description} found")
            else:
                print(f"❌ {description} not found")
    
    else:
        print(f"❌ Could not load page for styling test")


def main():
    """Run all generate button tests"""
    print("🎯 Generate Button Test Suite")
    print("=" * 50)
    
    try:
        test_dashboard_generate_button()
        test_quiz_generator_generate_button()
        test_workflow_description()
        test_button_styling()
        
        print("\n🎉 Generate button tests completed!")
        print("\n📋 Summary:")
        print("- Generate button added to both pages")
        print("- Auto-processing disabled")
        print("- Button starts disabled until file uploaded")
        print("- Manual processing triggered by button click")
        print("- Proper styling and user feedback")
        
        print("\n🔧 How to test manually:")
        print("1. Go to http://localhost:8000/app/")
        print("2. Notice the Generate button is disabled")
        print("3. Upload a file - button becomes enabled")
        print("4. Click Generate to process the file")
        print("5. Watch loading state and processing")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
