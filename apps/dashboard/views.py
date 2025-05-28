from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

@login_required(login_url='auth:signupin')
def home(request):
    """
    Render the home page of the dashboard.
    """
    # Get recent processing jobs for the user
    try:
        from apps.brain.models import ProcessingJob
        recent_jobs = ProcessingJob.objects.filter(user=request.user).order_by('-created_at')[:5]
    except:
        recent_jobs = []

    context = {
        'recent_jobs': recent_jobs
    }
    return render(request, "dashboard.html", context)

def logout_view(request):
    """
    Handle user logout
    """
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('auth:signupin')

@login_required(login_url='auth:signupin')
def profile(request):
    """
    Render the user profile page
    """
    return render(request, "profile.html")

@login_required(login_url='auth:signupin')
def settings(request):
    """
    Render the settings page
    """
    return render(request, "settings.html")

@login_required(login_url='auth:signupin')
def help(request):
    """
    Render the help and support page
    """
    return render(request, "help.html")

@login_required(login_url='auth:signupin')
def quiz_generator(request):
    """
    Render the quiz generator page
    """
    return render(request, "quiz_generator.html")

@login_required(login_url='auth:signupin')
def my_quizzes(request):
    """
    Render the my quizzes page with user's processing jobs
    """
    try:
        from apps.brain.models import ProcessingJob
        jobs = ProcessingJob.objects.filter(user=request.user).order_by('-created_at')
    except:
        jobs = []

    context = {
        'jobs': jobs
    }
    return render(request, "my_quizzes.html", context)

@login_required(login_url='auth:signupin')
def quiz_results(request, job_id):
    """
    Render the quiz results page for a specific job
    """
    try:
        from apps.brain.models import ProcessingJob
        from django.shortcuts import get_object_or_404

        job = get_object_or_404(ProcessingJob, id=job_id, user=request.user)
        qa_pairs = job.get_qa_pairs() if job.status == 'completed' else []
    except:
        job = None
        qa_pairs = []

    # Convert each QA pair to a dictionary (adjust keys to match actual attributes)
    serialized_qa_pairs = [
        {
            'question': qa.question,
            'answer': qa.answer,
        } for qa in qa_pairs
    ]

    return JsonResponse({
        'success': True,
        'job_id': job_id,
        'message': 'Document uploaded and processing started',
        'questions_generated': len(serialized_qa_pairs),
        'qa_pairs': serialized_qa_pairs,
    })

# API endpoints for AJAX calls
@login_required(login_url='auth:signupin')
@csrf_exempt
@require_http_methods(["POST"])
def api_process_document(request):
    """
    API endpoint to process documents via AJAX (OCR + Question Generation Pipeline)
    Handles file upload and storage using Django's file system
    """
    try:
        # Validate request
        if 'document' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No document file provided'
            }, status=400)

        uploaded_file = request.FILES['document']

        # Validate file type
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        file_extension = uploaded_file.name.lower().split('.')[-1]
        if f'.{file_extension}' not in allowed_extensions:
            return JsonResponse({
                'success': False,
                'error': 'Invalid file type. Please upload PDF, JPG, or PNG files.'
            }, status=400)

        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if uploaded_file.size > max_size:
            return JsonResponse({
                'success': False,
                'error': 'File size too large. Maximum size is 10MB.'
            }, status=400)

        # Get form data
        language = request.POST.get('language', 'auto')
        question_type = request.POST.get('question_type', 'MULTIPLECHOICE')
        num_questions = request.POST.get('num_questions')

        # Convert num_questions to int if provided
        if num_questions:
            try:
                num_questions = int(num_questions)
            except ValueError:
                num_questions = None

        # Import brain models and create job
        from apps.brain.models import ProcessingJob
        from django.core.files.storage import default_storage
        import os
        from pathlib import Path

        # Create processing job
        job = ProcessingJob.objects.create(
            user=request.user,
            document_name=uploaded_file.name,
            language=language,
            num_questions=num_questions,
            question_type=question_type,
            status='pending'
        )

        # Save uploaded file
        file_path = f'brain/uploads/{job.id}_{uploaded_file.name}'
        saved_path = default_storage.save(file_path, uploaded_file)

        # Update job with file path
        job.document_file = saved_path
        job.save()

        # Start processing in background (for now, we'll process immediately)
        try:
            job.status = 'processing'
            job.save()

            # Get full file path for processing
            full_file_path = default_storage.path(saved_path)

            # Import and use brain processor
            from apps.brain.brain_engine.processor import DocumentProcessor
            processor = DocumentProcessor(language=language)

            # Process document
            output_file = processor.process(full_file_path, num_questions=num_questions)

            # Load results and save to database
            import json
            with open(output_file, 'r', encoding='utf-8') as f:
                qa_data = json.load(f)

            # Save Q&A pairs to database
            from apps.brain.models import QuestionAnswer
            for qa_item in qa_data.get('questions', []):
                QuestionAnswer.objects.create(
                    job=job,
                    question=qa_item.get('question', ''),
                    answer=qa_item.get('answer', ''),
                    question_type=question_type,
                    options=qa_item.get('options', []),
                    correct_option=qa_item.get('correct_option', ''),
                    confidence_score=qa_item.get('confidence_score'),
                    source_text=qa_item.get('source_text', '')
                )

            # Save output file path
            output_filename = f'brain/qa_outputs/{job.id}_results.json'
            with open(default_storage.path(output_filename), 'w', encoding='utf-8') as f:
                json.dump(qa_data, f, ensure_ascii=False, indent=2)
            job.output_file = output_filename

            # Mark job as completed
            job.mark_completed()

            return JsonResponse({
                'success': True,
                'job_id': job.id,
                'message': 'Document uploaded and processing started',
                'questions_generated': len(qa_data.get('questions', []))
            })

        except Exception as processing_error:
            # Mark job as failed
            job.mark_failed(str(processing_error))
            return JsonResponse({
                'success': False,
                'error': f'Processing failed: {str(processing_error)}'
            }, status=500)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }, status=500)

@login_required(login_url='auth:signupin')
def api_job_status(request, job_id):
    """
    API endpoint to get job status
    """
    try:
        from apps.brain.views import get_job_status
        return get_job_status(request, job_id)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Brain processing not available: {str(e)}'
        }, status=500)