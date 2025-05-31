from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

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

def logout_redirect(request):
    """Redirect to auth logout"""
    return redirect('auth:logout')

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

    # Convert each QA pair to a dictionary with full details
    serialized_qa_pairs = []
    for qa in qa_pairs:
        qa_dict = {
            'question': qa.question,
            'answer': qa.answer,
            'question_type': qa.question_type,
        }

        # Add multiple choice specific fields
        if qa.question_type == 'MULTIPLECHOICE' and qa.options:
            qa_dict['options'] = qa.options
            qa_dict['correct_option'] = qa.correct_option

        # Add metadata if available
        if qa.confidence_score is not None:
            qa_dict['confidence_score'] = qa.confidence_score

        serialized_qa_pairs.append(qa_dict)

    # Prepare form settings and detected values
    form_settings = {}
    detected_values = {}
    generated_values = {}

    if job:
        # Form settings (what user selected)
        form_settings = {
            'selected_language': job.language,
            'selected_question_type': job.question_type,
            'selected_num_questions': job.num_questions,
            'selected_document_type': job.document_type,
        }

        # Detected values (what system detected)
        metadata = job.processing_metadata or {}
        detected_values = {
            'detected_language': metadata.get('language', 'unknown'),
            'detected_document_type': metadata.get('doc_type', 'unknown'),
            'detected_is_question_paper': metadata.get('is_question_paper', False),
            'detected_pdf_type': metadata.get('pdf_type'),
            'file_size': metadata.get('file_size'),
            'file_extension': metadata.get('extension'),
        }

        # Add human-readable labels
        form_settings['selected_language_display'] = dict(job.LANGUAGE_CHOICES).get(job.language, job.language)
        form_settings['selected_question_type_display'] = dict(job.QUESTION_TYPE_CHOICES).get(job.question_type, job.question_type)

        detected_values['detected_language_display'] = {
            'bengali': 'Bengali', 'english': 'English', 'unknown': 'Unknown'
        }.get(detected_values['detected_language'], detected_values['detected_language'])

        # Generated values (actual results)
        generated_values = {
            'generated_num_questions': len(serialized_qa_pairs),
            'generated_question_types': list(set(qa.question_type for qa in qa_pairs)),
            'processing_status': job.status,
            'processing_time': (job.completed_at - job.created_at).total_seconds() if job.completed_at else None,
        }

    return JsonResponse({
        'success': True,
        'job_id': job_id,
        'message': 'Quiz results retrieved successfully',
        'questions_generated': len(serialized_qa_pairs),
        'qa_pairs': serialized_qa_pairs,
        'form_settings': form_settings,
        'detected_values': detected_values,
        'generated_values': generated_values,
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

            # Import document detector and detect metadata first
            from apps.brain.brain_engine.utils.document_detector import detect_document_type
            document_metadata = detect_document_type(full_file_path)

            # Store detection metadata in job
            job.processing_metadata = document_metadata
            job.document_type = document_metadata.get('doc_type', 'unknown')
            job.is_question_paper = document_metadata.get('is_question_paper', False)
            job.save()

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

            # Prepare form settings and detected values for response
            form_settings = {
                'selected_language': language,
                'selected_question_type': question_type,
                'selected_num_questions': num_questions,
            }

            detected_values = {
                'detected_language': document_metadata.get('language', 'unknown'),
                'detected_document_type': document_metadata.get('doc_type', 'unknown'),
                'detected_is_question_paper': document_metadata.get('is_question_paper', False),
                'detected_pdf_type': document_metadata.get('pdf_type'),
                'file_size': document_metadata.get('file_size'),
                'file_extension': document_metadata.get('extension'),
            }

            return JsonResponse({
                'success': True,
                'job_id': job.id,
                'message': 'Document processed successfully',
                'questions_generated': len(qa_data.get('questions', [])),
                'form_settings': form_settings,
                'detected_values': detected_values,
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