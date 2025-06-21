#!/usr/bin/env python
"""
Test script for Discord webhook functionality
"""
import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from apps.brain.models import ProcessingJob
from apps.utils import send_document_processing_success_webhook, send_document_processing_failed_webhook

def test_webhook():
    """Test the webhook functionality"""
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='test_webhook_user',
        defaults={
            'email': 'test@gmail.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    # Create a test job
    job = ProcessingJob.objects.create(
        user=user,
        document_name='test_document.pdf',
        language='auto',
        question_type='MULTIPLECHOICE',
        num_questions=5,
        document_type='pdf',
        is_question_paper=True,
        status='completed'
    )
    job.mark_completed()
    
    # Test data with questions
    qa_data_success = {
        'questions': [
            {
                'question': 'What is the capital of France?',
                'options': [
                    {'key': 'A', 'text': 'London'},
                    {'key': 'B', 'text': 'Berlin'},
                    {'key': 'C', 'text': 'Paris'},
                    {'key': 'D', 'text': 'Madrid'}
                ],
                'answer': 'Paris',
                'correct_option': 'C',
                'type': 'MULTIPLECHOICE'
            },
            {
                'question': 'What is 2 + 2?',
                'options': [
                    {'key': 'A', 'text': '3'},
                    {'key': 'B', 'text': '4'},
                    {'key': 'C', 'text': '5'},
                    {'key': 'D', 'text': '6'}
                ],
                'answer': '4',
                'correct_option': 'B',
                'type': 'MULTIPLECHOICE'
            }
        ],
        'metadata': {
            'language': 'auto',
            'question_type': 'MULTIPLECHOICE',
            'source_document': 'test_document.pdf'
        }
    }
    
    # Test data with no questions (should trigger failure)
    qa_data_failure = {
        'questions': [],
        'metadata': {
            'language': 'auto',
            'question_type': 'MULTIPLECHOICE',
            'source_document': 'test_document.pdf'
        }
    }
    
    print("🧪 Testing Discord Webhook Functionality")
    print("=" * 50)
    
    # Test 1: Success webhook with questions
    print("\n📡 Test 1: Success webhook (2 questions)")
    result1 = send_document_processing_success_webhook(
        user=user,
        job=job,
        questions_count=2,
        qa_data=qa_data_success
    )
    print(f"Result: {result1}")
    
    # Test 2: Failure webhook (0 questions should trigger failure)
    print("\n📡 Test 2: Failure webhook (0 questions)")
    result2 = send_document_processing_success_webhook(
        user=user,
        job=job,
        questions_count=0,
        qa_data=qa_data_failure
    )
    print(f"Result: {result2}")
    
    # Test 3: Direct failure webhook
    print("\n📡 Test 3: Direct failure webhook")
    result3 = send_document_processing_failed_webhook(
        user=user,
        job=job,
        error_message="Test error: Document could not be processed",
        qa_data=qa_data_failure
    )
    print(f"Result: {result3}")
    
    print("\n✅ Webhook testing completed!")
    print(f"📝 Test job ID: {job.id}")
    
    # Clean up
    job.delete()
    if created:
        user.delete()

if __name__ == '__main__':
    test_webhook()
