from celery import Celery, current_task
from celery.result import AsyncResult
from django.conf import settings
import time
import json
from .models import ProcessingJob, QuestionAnswer
from .brain_processor import BrainProcessor

app = Celery('sisimpur')

@app.task(bind=True)
def process_document_with_progress(self, job_id, file_path, config):
    """
    Process document with real-time progress updates
    """
    try:
        # Get the job
        job = ProcessingJob.objects.get(id=job_id)
        
        # Stage 1: Upload Complete (15%)
        self.update_state(
            state='PROGRESS',
            meta={
                'stage': 'upload',
                'progress': 15,
                'title': 'Upload Complete',
                'message': 'Document uploaded successfully. Starting analysis...',
                'time_estimate': '45-60 seconds remaining'
            }
        )
        time.sleep(2)  # Simulate upload processing time
        
        # Stage 2: Analyzing Content (45%)
        self.update_state(
            state='PROGRESS',
            meta={
                'stage': 'analyze',
                'progress': 45,
                'title': 'Analyzing Content',
                'message': 'AI is reading and understanding your document...',
                'time_estimate': '30-45 seconds remaining'
            }
        )
        
        # Initialize brain processor
        processor = BrainProcessor()
        
        # Extract text with progress updates
        for i in range(3):
            time.sleep(3)  # Simulate text extraction
            progress = 45 + (i + 1) * 5  # 45% -> 60%
            self.update_state(
                state='PROGRESS',
                meta={
                    'stage': 'analyze',
                    'progress': progress,
                    'title': 'Analyzing Content',
                    'message': f'Processing page {i + 1}... Understanding document structure...',
                    'time_estimate': f'{30 - (i * 5)}-{45 - (i * 5)} seconds remaining'
                }
            )
        
        # Extract text from document
        text_content = processor.extract_text(file_path)
        
        # Stage 3: Generating Questions (85%)
        self.update_state(
            state='PROGRESS',
            meta={
                'stage': 'generate',
                'progress': 70,
                'title': 'Generating Questions',
                'message': 'Creating intelligent questions from your content...',
                'time_estimate': '15-20 seconds remaining'
            }
        )
        
        # Generate questions with progress
        questions_data = processor.generate_questions(
            text_content, 
            config,
            progress_callback=lambda p: self.update_state(
                state='PROGRESS',
                meta={
                    'stage': 'generate',
                    'progress': 70 + (p * 0.15),  # 70% -> 85%
                    'title': 'Generating Questions',
                    'message': f'Generated {int(p * config.get("num_questions", 10) / 100)} questions...',
                    'time_estimate': f'{15 - int(p * 0.15)} seconds remaining'
                }
            )
        )
        
        # Stage 4: Saving to Database (95%)
        self.update_state(
            state='PROGRESS',
            meta={
                'stage': 'complete',
                'progress': 90,
                'title': 'Saving Questions',
                'message': 'Storing questions in database...',
                'time_estimate': '5 seconds remaining'
            }
        )
        
        # Save questions to database
        questions_created = 0
        for i, question_data in enumerate(questions_data):
            QuestionAnswer.objects.create(
                processing_job=job,
                question=question_data['question'],
                answer=question_data['answer'],
                options=question_data.get('options', []),
                question_type=question_data.get('type', 'MULTIPLECHOICE'),
                difficulty=question_data.get('difficulty', 'MEDIUM')
            )
            questions_created += 1
            
            # Update progress for each question saved
            progress = 90 + (i + 1) * (5 / len(questions_data))
            self.update_state(
                state='PROGRESS',
                meta={
                    'stage': 'complete',
                    'progress': progress,
                    'title': 'Saving Questions',
                    'message': f'Saved {questions_created} of {len(questions_data)} questions...',
                    'time_estimate': f'{len(questions_data) - questions_created} questions remaining'
                }
            )
            time.sleep(0.5)  # Small delay for visual effect
        
        # Final completion (100%)
        job.status = 'completed'
        job.save()
        
        return {
            'stage': 'complete',
            'progress': 100,
            'title': 'Success!',
            'message': f'Successfully generated {questions_created} questions from your document!',
            'time_estimate': 'Complete!',
            'questions_generated': questions_created,
            'job_id': job_id,
            'success': True
        }
        
    except Exception as e:
        # Update job status to failed
        job.status = 'failed'
        job.error_message = str(e)
        job.save()
        
        self.update_state(
            state='FAILURE',
            meta={
                'stage': 'error',
                'progress': 0,
                'title': 'Processing Failed',
                'message': f'Error: {str(e)}',
                'time_estimate': 'Failed',
                'success': False,
                'error': str(e)
            }
        )
        raise


def get_task_progress(task_id):
    """
    Get current progress of a Celery task
    """
    result = AsyncResult(task_id)
    
    if result.state == 'PENDING':
        return {
            'state': 'PENDING',
            'stage': 'upload',
            'progress': 0,
            'title': 'Starting...',
            'message': 'Preparing to process your document...',
            'time_estimate': 'Estimating time...'
        }
    elif result.state == 'PROGRESS':
        return {
            'state': 'PROGRESS',
            **result.info
        }
    elif result.state == 'SUCCESS':
        return {
            'state': 'SUCCESS',
            **result.result
        }
    elif result.state == 'FAILURE':
        return {
            'state': 'FAILURE',
            'stage': 'error',
            'progress': 0,
            'title': 'Processing Failed',
            'message': str(result.info),
            'time_estimate': 'Failed',
            'success': False,
            'error': str(result.info)
        }
    
    return {
        'state': result.state,
        'stage': 'unknown',
        'progress': 0,
        'title': 'Unknown State',
        'message': 'Processing status unknown',
        'time_estimate': 'Unknown'
    }
