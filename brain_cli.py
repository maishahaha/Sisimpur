#!/usr/bin/env python3
"""
Sisimpur Brain CLI Tool for Development Testing

This CLI tool allows you to test the brain functionality quickly during development.
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.contrib.auth.models import User
from apps.brain.models import ProcessingJob, QuestionAnswer


def create_test_user():
    """Create a test user for CLI operations"""
    user, created = User.objects.get_or_create(
        username='test_user',
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


def process_document(file_path, num_questions=None, language='auto', question_type='MULTIPLECHOICE'):
    """Process a document and generate questions"""
    try:
        from apps.brain.brain_engine.processor import DocumentProcessor
        
        print(f"🧠 Processing document: {file_path}")
        print(f"   Language: {language}")
        print(f"   Question Type: {question_type}")
        print(f"   Number of Questions: {num_questions or 'Auto'}")
        print()
        
        # Create test user
        user = create_test_user()
        
        # Create processing job
        job = ProcessingJob.objects.create(
            user=user,
            document_name=Path(file_path).name,
            language=language,
            num_questions=num_questions,
            question_type=question_type,
            status='processing'
        )
        
        print(f"📝 Created job #{job.id}")
        
        # Initialize processor
        processor = DocumentProcessor(language=language)
        
        # Process document
        output_file = processor.process(file_path, num_questions=num_questions)
        
        # Load results
        with open(output_file, 'r', encoding='utf-8') as f:
            qa_data = json.load(f)
        
        # Save to database
        for qa_item in qa_data.get('questions', []):
            QuestionAnswer.objects.create(
                job=job,
                question=qa_item.get('question', ''),
                answer=qa_item.get('answer', ''),
                question_type=question_type,
                options=qa_item.get('options', []),
                correct_option=qa_item.get('correct_option', ''),
                confidence_score=qa_item.get('confidence_score')
            )
        
        job.mark_completed()
        
        print(f"✅ Processing completed!")
        print(f"   Generated: {len(qa_data.get('questions', []))} questions")
        print(f"   Output file: {output_file}")
        print(f"   Job ID: {job.id}")
        print()
        
        return job, qa_data
        
    except Exception as e:
        print(f"❌ Error processing document: {e}")
        if 'job' in locals():
            job.mark_failed(str(e))
        raise


def list_jobs():
    """List all processing jobs"""
    jobs = ProcessingJob.objects.all().order_by('-created_at')
    
    if not jobs:
        print("📝 No processing jobs found")
        return
    
    print("📋 Processing Jobs:")
    print("-" * 80)
    print(f"{'ID':<5} {'Document':<30} {'Status':<12} {'Questions':<10} {'Created':<20}")
    print("-" * 80)
    
    for job in jobs:
        qa_count = job.get_qa_pairs().count() if job.status == 'completed' else '-'
        print(f"{job.id:<5} {job.document_name[:29]:<30} {job.status:<12} {qa_count:<10} {job.created_at.strftime('%Y-%m-%d %H:%M'):<20}")


def show_results(job_id):
    """Show results for a specific job"""
    try:
        job = ProcessingJob.objects.get(id=job_id)
        
        print(f"📄 Job #{job.id}: {job.document_name}")
        print(f"   Status: {job.status}")
        print(f"   Language: {job.language}")
        print(f"   Question Type: {job.question_type}")
        print(f"   Created: {job.created_at}")
        
        if job.status == 'completed':
            qa_pairs = job.get_qa_pairs()
            print(f"   Questions: {qa_pairs.count()}")
            print()
            
            for i, qa in enumerate(qa_pairs, 1):
                print(f"Q{i}: {qa.question}")
                
                if qa.question_type == 'MULTIPLECHOICE' and qa.options:
                    for option in qa.options:
                        marker = "✓" if option.startswith(qa.correct_option) else " "
                        print(f"   {marker} {option}")
                
                print(f"A: {qa.answer}")
                
                if qa.confidence_score:
                    print(f"   Confidence: {qa.confidence_score:.1f}%")
                
                print()
        
        elif job.status == 'failed':
            print(f"   Error: {job.error_message}")
        
    except ProcessingJob.DoesNotExist:
        print(f"❌ Job #{job_id} not found")


def main():
    parser = argparse.ArgumentParser(description='Sisimpur Brain CLI Tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process a document')
    process_parser.add_argument('file', help='Path to document file')
    process_parser.add_argument('-n', '--num-questions', type=int, help='Number of questions to generate')
    process_parser.add_argument('-l', '--language', default='auto', choices=['auto', 'english', 'bengali'], help='Language for processing')
    process_parser.add_argument('-t', '--type', default='MULTIPLECHOICE', choices=['MULTIPLECHOICE', 'SHORT'], help='Question type')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all processing jobs')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show results for a specific job')
    show_parser.add_argument('job_id', type=int, help='Job ID to show')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run a quick test with sample data')
    
    args = parser.parse_args()
    
    if args.command == 'process':
        if not os.path.exists(args.file):
            print(f"❌ File not found: {args.file}")
            return
        
        process_document(
            args.file,
            num_questions=args.num_questions,
            language=args.language,
            question_type=args.type
        )
    
    elif args.command == 'list':
        list_jobs()
    
    elif args.command == 'show':
        show_results(args.job_id)
    
    elif args.command == 'test':
        print("🧪 Running quick test...")
        print("This would process a sample document if available.")
        print("Usage: python brain_cli.py process path/to/document.pdf")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
