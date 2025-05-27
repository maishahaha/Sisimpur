from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import json
import logging
import os
import tempfile
from pathlib import Path

from .models import ProcessingJob, QuestionAnswer
# Import DocumentProcessor only when needed to avoid hanging during Django startup

logger = logging.getLogger("sisimpur.brain.views")


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def process_document(request):
    """
    Process uploaded document and generate Q&A pairs.
    """
    try:
        # Get form data
        document_file = request.FILES.get('document')
        num_questions = request.POST.get('num_questions')
        language = request.POST.get('language', 'auto')
        question_type = request.POST.get('question_type', 'MULTIPLECHOICE')

        if not document_file:
            return JsonResponse({
                'success': False,
                'error': 'No document file provided'
            }, status=400)

        # Validate file type
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.txt']
        file_ext = Path(document_file.name).suffix.lower()
        if file_ext not in allowed_extensions:
            return JsonResponse({
                'success': False,
                'error': f'Unsupported file type: {file_ext}. Allowed: {", ".join(allowed_extensions)}'
            }, status=400)

        # Convert num_questions to int if provided
        if num_questions:
            try:
                num_questions = int(num_questions)
                if num_questions <= 0:
                    raise ValueError("Number of questions must be positive")
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid number of questions'
                }, status=400)

        # Create processing job
        job = ProcessingJob.objects.create(
            user=request.user,
            document_name=document_file.name,
            language=language,
            num_questions=num_questions,
            question_type=question_type,
            status='pending'
        )

        # Save uploaded file
        file_path = default_storage.save(
            f'brain/uploads/{job.id}_{document_file.name}',
            ContentFile(document_file.read())
        )
        job.document_file = file_path
        job.save()

        # Process the document
        try:
            job.status = 'processing'
            job.save()

            # Get full file path
            full_file_path = default_storage.path(file_path)

            # Initialize processor
            from .brain_engine.processor import DocumentProcessor
            processor = DocumentProcessor(language=language)

            # Process document
            if file_ext == '.txt':
                # Handle text files
                with open(full_file_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
                output_file = processor.process_text(
                    text_content,
                    num_questions=num_questions,
                    source_name=document_file.name
                )
            else:
                # Handle PDF and image files
                output_file = processor.process(full_file_path, num_questions=num_questions)

            # Load the generated Q&A pairs
            with open(output_file, 'r', encoding='utf-8') as f:
                qa_data = json.load(f)

            # Save Q&A pairs to database
            for qa_item in qa_data.get('questions', []):
                question_answer = QuestionAnswer.objects.create(
                    job=job,
                    question=qa_item.get('question', ''),
                    answer=qa_item.get('answer', ''),
                    question_type=question_type,
                    options=qa_item.get('options', []),
                    correct_option=qa_item.get('correct_option', ''),
                    confidence_score=qa_item.get('confidence_score')
                )

            # Save output file path
            relative_output_path = os.path.relpath(output_file, settings.MEDIA_ROOT)
            job.output_file = relative_output_path
            job.mark_completed()

            return JsonResponse({
                'success': True,
                'job_id': job.id,
                'message': f'Successfully generated {len(qa_data.get("questions", []))} questions',
                'qa_count': len(qa_data.get('questions', []))
            })

        except Exception as e:
            logger.error(f"Error processing document for job {job.id}: {e}")
            job.mark_failed(str(e))
            return JsonResponse({
                'success': False,
                'error': f'Processing failed: {str(e)}'
            }, status=500)

    except Exception as e:
        logger.error(f"Error in process_document view: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def process_text(request):
    """
    Process raw text and generate Q&A pairs.
    """
    try:
        data = json.loads(request.body)

        text = data.get('text', '').strip()
        num_questions = data.get('num_questions')
        language = data.get('language', 'auto')
        question_type = data.get('question_type', 'MULTIPLECHOICE')

        if not text:
            return JsonResponse({
                'success': False,
                'error': 'No text provided'
            }, status=400)

        # Convert num_questions to int if provided
        if num_questions:
            try:
                num_questions = int(num_questions)
                if num_questions <= 0:
                    raise ValueError("Number of questions must be positive")
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid number of questions'
                }, status=400)

        # Create processing job
        job = ProcessingJob.objects.create(
            user=request.user,
            document_name="Raw Text Input",
            language=language,
            num_questions=num_questions,
            question_type=question_type,
            status='processing',
            document_type='text'
        )

        try:
            # Initialize processor
            from .brain_engine.processor import DocumentProcessor
            processor = DocumentProcessor(language=language)

            # Process text
            output_file = processor.process_text(
                text,
                num_questions=num_questions,
                source_name=f"text_input_{job.id}"
            )

            # Load the generated Q&A pairs
            with open(output_file, 'r', encoding='utf-8') as f:
                qa_data = json.load(f)

            # Save Q&A pairs to database
            for qa_item in qa_data.get('questions', []):
                question_answer = QuestionAnswer.objects.create(
                    job=job,
                    question=qa_item.get('question', ''),
                    answer=qa_item.get('answer', ''),
                    question_type=question_type,
                    options=qa_item.get('options', []),
                    correct_option=qa_item.get('correct_option', ''),
                    confidence_score=qa_item.get('confidence_score')
                )

            # Save output file path
            relative_output_path = os.path.relpath(output_file, settings.MEDIA_ROOT)
            job.output_file = relative_output_path
            job.mark_completed()

            return JsonResponse({
                'success': True,
                'job_id': job.id,
                'message': f'Successfully generated {len(qa_data.get("questions", []))} questions',
                'qa_count': len(qa_data.get('questions', []))
            })

        except Exception as e:
            logger.error(f"Error processing text for job {job.id}: {e}")
            job.mark_failed(str(e))
            return JsonResponse({
                'success': False,
                'error': f'Processing failed: {str(e)}'
            }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in process_text view: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=500)


@login_required
def get_job_status(request, job_id):
    """
    Get the status of a processing job.
    """
    try:
        job = get_object_or_404(ProcessingJob, id=job_id, user=request.user)

        response_data = {
            'job_id': job.id,
            'status': job.status,
            'document_name': job.document_name,
            'created_at': job.created_at.isoformat(),
            'updated_at': job.updated_at.isoformat(),
        }

        if job.completed_at:
            response_data['completed_at'] = job.completed_at.isoformat()

        if job.status == 'failed':
            response_data['error_message'] = job.error_message

        if job.status == 'completed':
            qa_pairs = job.get_qa_pairs()
            response_data['qa_count'] = qa_pairs.count()
            response_data['questions'] = [qa.to_dict() for qa in qa_pairs]

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Error getting job status for job {job_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=500)


@login_required
def get_job_results(request, job_id):
    """
    Get the Q&A results for a completed job.
    """
    try:
        job = get_object_or_404(ProcessingJob, id=job_id, user=request.user)

        if job.status != 'completed':
            return JsonResponse({
                'success': False,
                'error': 'Job is not completed yet'
            }, status=400)

        qa_pairs = job.get_qa_pairs()

        return JsonResponse({
            'success': True,
            'job_id': job.id,
            'document_name': job.document_name,
            'qa_count': qa_pairs.count(),
            'questions': [qa.to_dict() for qa in qa_pairs],
            'generated_at': job.completed_at.isoformat() if job.completed_at else None
        })

    except Exception as e:
        logger.error(f"Error getting job results for job {job_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=500)


@login_required
def download_results(request, job_id):
    """
    Download Q&A results as JSON file.
    """
    try:
        from django.http import HttpResponse

        job = get_object_or_404(ProcessingJob, id=job_id, user=request.user)

        if job.status != 'completed':
            return JsonResponse({
                'success': False,
                'error': 'Job is not completed yet'
            }, status=400)

        qa_pairs = job.get_qa_pairs()

        # Prepare data for download
        download_data = {
            'source_document': job.document_name,
            'generated_at': job.completed_at.isoformat() if job.completed_at else None,
            'language': job.language,
            'question_type': job.question_type,
            'total_questions': qa_pairs.count(),
            'questions': [qa.to_dict() for qa in qa_pairs]
        }

        # Create response
        response = HttpResponse(
            json.dumps(download_data, ensure_ascii=False, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="{job.document_name}_qa_results.json"'

        return response

    except Exception as e:
        logger.error(f"Error downloading results for job {job_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=500)


@login_required
def list_jobs(request):
    """
    List all processing jobs for the current user.
    """
    try:
        jobs = ProcessingJob.objects.filter(user=request.user).order_by('-created_at')

        jobs_data = []
        for job in jobs:
            job_data = {
                'id': job.id,
                'document_name': job.document_name,
                'status': job.status,
                'language': job.language,
                'question_type': job.question_type,
                'created_at': job.created_at.isoformat(),
                'updated_at': job.updated_at.isoformat(),
            }

            if job.completed_at:
                job_data['completed_at'] = job.completed_at.isoformat()

            if job.status == 'completed':
                job_data['qa_count'] = job.get_qa_pairs().count()

            if job.status == 'failed':
                job_data['error_message'] = job.error_message

            jobs_data.append(job_data)

        return JsonResponse({
            'success': True,
            'jobs': jobs_data
        })

    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=500)


# Development/Testing endpoints
@login_required
def dev_test_processing(request):
    """
    Development endpoint for quick testing (JSON response)
    Usage: GET /api/brain/dev/test/?file=path/to/file.pdf&questions=5
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Admin access required'}, status=403)

    file_path = request.GET.get('file')
    num_questions = request.GET.get('questions', 5)
    language = request.GET.get('language', 'auto')
    question_type = request.GET.get('type', 'MULTIPLECHOICE')

    if not file_path:
        return JsonResponse({'error': 'file parameter required'}, status=400)

    try:
        from .brain_engine.processor import DocumentProcessor
        import tempfile
        import json

        # Create a temporary job for testing
        job = ProcessingJob.objects.create(
            user=request.user,
            document_name=f"dev_test_{file_path.split('/')[-1]}",
            language=language,
            num_questions=int(num_questions),
            question_type=question_type,
            status='processing'
        )

        # Process the document
        processor = DocumentProcessor(language=language)
        output_file = processor.process(file_path, num_questions=int(num_questions))

        # Load and return results
        with open(output_file, 'r', encoding='utf-8') as f:
            qa_data = json.load(f)

        job.mark_completed()

        return JsonResponse({
            'success': True,
            'job_id': job.id,
            'file_processed': file_path,
            'questions_generated': len(qa_data.get('questions', [])),
            'results': qa_data
        })

    except Exception as e:
        if 'job' in locals():
            job.mark_failed(str(e))
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def dev_list_jobs(request):
    """
    Development endpoint to list jobs as JSON
    Usage: GET /api/brain/dev/jobs/
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Admin access required'}, status=403)

    jobs = ProcessingJob.objects.all().order_by('-created_at')[:20]  # Last 20 jobs

    jobs_data = []
    for job in jobs:
        job_data = {
            'id': job.id,
            'document_name': job.document_name,
            'status': job.status,
            'language': job.language,
            'question_type': job.question_type,
            'created_at': job.created_at.isoformat(),
            'questions_count': job.get_qa_pairs().count() if job.status == 'completed' else 0
        }

        if job.status == 'failed':
            job_data['error'] = job.error_message

        jobs_data.append(job_data)

    return JsonResponse({
        'success': True,
        'jobs': jobs_data,
        'total': jobs.count()
    })


@login_required
@require_http_methods(["DELETE"])
def delete_job(request, job_id):
    """
    Delete a processing job and its associated data
    """
    try:
        job = get_object_or_404(ProcessingJob, id=job_id, user=request.user)

        # Store job info for response
        job_name = job.document_name

        # Delete associated files
        if job.document_file:
            try:
                job.document_file.delete(save=False)
            except Exception as e:
                logger.warning(f"Failed to delete document file for job {job_id}: {e}")

        if job.extracted_text_file:
            try:
                job.extracted_text_file.delete(save=False)
            except Exception as e:
                logger.warning(f"Failed to delete extracted text file for job {job_id}: {e}")

        if job.output_file:
            try:
                job.output_file.delete(save=False)
            except Exception as e:
                logger.warning(f"Failed to delete output file for job {job_id}: {e}")

        # Delete Q&A pairs (will be deleted automatically due to foreign key cascade)
        qa_count = job.get_qa_pairs().count()

        # Delete the job
        job.delete()

        logger.info(f"Deleted job {job_id} ({job_name}) with {qa_count} Q&A pairs")

        return JsonResponse({
            'success': True,
            'message': f'Quiz "{job_name}" deleted successfully'
        })

    except ProcessingJob.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Quiz not found'
        }, status=404)

    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to delete quiz'
        }, status=500)