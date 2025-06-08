from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib import messages
import uuid
import random
import json
from .models import ExamSession

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
        from .models import ExamSession, ExamConfiguration

        jobs = ProcessingJob.objects.filter(user=request.user).order_by('-created_at')

        # Add latest exam session info for results (no attempt limits)
        for job in jobs:
            # Get the latest exam session for results only
            latest_exam = ExamSession.objects.filter(
                user=request.user,
                processing_job=job
            ).order_by('-started_at').first()

            job.latest_exam = latest_exam
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


# ============================================================================
# LEADERBOARD FUNCTIONALITY
# ============================================================================

@login_required(login_url='auth:signupin')
def leaderboard(request):
    """
    Display global leaderboard with user rankings based on exam performance
    """
    from django.db.models import Count, Avg, Sum, Q
    from django.contrib.auth.models import User
    from datetime import datetime, timedelta

    # Get filter parameter
    filter_type = request.GET.get('filter', 'all')

    # Calculate date range based on filter
    now = timezone.now()
    if filter_type == 'week':
        start_date = now - timedelta(days=7)
    elif filter_type == 'month':
        start_date = now - timedelta(days=30)
    elif filter_type == 'year':
        start_date = now - timedelta(days=365)
    else:
        start_date = None

    # Base queryset for exam sessions
    exam_sessions = ExamSession.objects.filter(status='completed')
    if start_date:
        exam_sessions = exam_sessions.filter(completed_at__gte=start_date)

    # Calculate user statistics
    user_stats = User.objects.annotate(
        total_exams=Count('exam_sessions', filter=Q(exam_sessions__in=exam_sessions)),
        total_score=Sum('exam_sessions__total_score', filter=Q(exam_sessions__in=exam_sessions)),
        avg_percentage=Avg('exam_sessions__percentage_score', filter=Q(exam_sessions__in=exam_sessions)),
        total_credit_points=Sum('exam_sessions__credit_points', filter=Q(exam_sessions__in=exam_sessions))
    ).filter(
        total_exams__gt=0  # Only users who have taken exams
    ).order_by('-total_score', '-avg_percentage', '-total_exams')

    # Add rank and badge to each user
    leaderboard_data = []
    for rank, user in enumerate(user_stats, 1):
        # Determine badge based on performance
        avg_score = user.avg_percentage or 0
        total_exams = user.total_exams or 0

        if avg_score >= 95 and total_exams >= 20:
            badge = 'champion'
            badge_label = 'Champion'
        elif avg_score >= 90 and total_exams >= 15:
            badge = 'expert'
            badge_label = 'Expert'
        elif avg_score >= 85 and total_exams >= 10:
            badge = 'master'
            badge_label = 'Master'
        elif avg_score >= 75 and total_exams >= 5:
            badge = 'pro'
            badge_label = 'Pro'
        else:
            badge = 'beginner'
            badge_label = 'Beginner'

        # Determine user title based on performance
        if avg_score >= 95:
            title = 'Quiz Master'
        elif avg_score >= 90:
            title = 'Knowledge Seeker'
        elif avg_score >= 85:
            title = 'Study Enthusiast'
        elif avg_score >= 75:
            title = 'Quick Learner'
        elif avg_score >= 65:
            title = 'Rising Star'
        else:
            title = 'Knowledge Hunter'

        leaderboard_data.append({
            'rank': rank,
            'user': user,
            'title': title,
            'total_score': user.total_score or 0,
            'total_exams': total_exams,
            'avg_percentage': round(avg_score, 1) if avg_score else 0,
            'total_credit_points': user.total_credit_points or 0,
            'badge': badge,
            'badge_label': badge_label,
            'is_current_user': user == request.user
        })

    # Calculate global statistics
    total_users = User.objects.filter(exam_sessions__status='completed').distinct().count()
    active_users_week = User.objects.filter(
        exam_sessions__status='completed',
        exam_sessions__completed_at__gte=now - timedelta(days=7)
    ).distinct().count()
    total_exams_completed = ExamSession.objects.filter(status='completed').count()

    # Find current user's position
    current_user_rank = None
    current_user_data = None
    for item in leaderboard_data:
        if item['is_current_user']:
            current_user_rank = item['rank']
            current_user_data = item
            break

    context = {
        'leaderboard_data': leaderboard_data[:50],  # Top 50 users
        'current_user_rank': current_user_rank,
        'current_user_data': current_user_data,
        'filter_type': filter_type,
        'total_users': total_users,
        'active_users_week': active_users_week,
        'total_exams_completed': total_exams_completed,
    }

    return render(request, 'leaderboard.html', context)


# ============================================================================
# EXAM FUNCTIONALITY
# ============================================================================

@login_required(login_url='auth:signupin')
def start_exam(request, job_id):
    """
    Start a new exam session for a completed processing job
    """
    print(f"DEBUG: start_exam called with job_id={job_id}, user={request.user}")
    try:
        from apps.brain.models import ProcessingJob
        from .models import ExamSession, ExamConfiguration

        # Get the processing job
        job = get_object_or_404(ProcessingJob, id=job_id, user=request.user)
        print(f"DEBUG: Found job: {job}, status: {job.status}")

        if job.status != 'completed':
            print(f"DEBUG: Job not completed, redirecting to my_quizzes")
            messages.error(request, 'Cannot start exam for incomplete quiz.')
            return redirect('dashboard:my_quizzes')

        # Get questions
        qa_pairs = job.get_qa_pairs()
        print(f"DEBUG: Found {qa_pairs.count()} questions")
        if not qa_pairs.exists():
            print(f"DEBUG: No questions found, redirecting to my_quizzes")
            messages.error(request, 'No questions found for this quiz.')
            return redirect('dashboard:my_quizzes')

        # Get configuration
        config = ExamConfiguration.get_current_config()
        print(f"DEBUG: Got config: {config}")

        # Create new exam session (no attempt restrictions)
        session_id = str(uuid.uuid4())
        questions_list = list(qa_pairs.values_list('id', flat=True))
        random.shuffle(questions_list)  # Randomize question order
        print(f"DEBUG: Created session_id: {session_id}")
        print(f"DEBUG: Questions list: {questions_list}")

        # Get the next attempt number to avoid unique constraint violation
        user_attempts = ExamSession.objects.filter(
            user=request.user,
            processing_job=job
        ).count()
        next_attempt_number = user_attempts + 1
        print(f"DEBUG: Next attempt number: {next_attempt_number}")

        exam_session = ExamSession.objects.create(
            user=request.user,
            processing_job=job,
            session_id=session_id,
            total_questions=len(questions_list),
            time_limit_minutes=len(questions_list) * config.default_time_per_question_minutes,
            allow_navigation=config.allow_question_navigation,
            max_attempts=999,  # Unlimited
            attempt_number=next_attempt_number,
            questions_order=questions_list
        )
        print(f"DEBUG: Created exam session: {exam_session}")
        print(f"DEBUG: Redirecting to exam_session with session_id: {session_id}")

        return redirect('dashboard:exam_session', session_id=session_id)

    except Exception as e:
        print(f"DEBUG: Exception in start_exam: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        messages.error(request, f'Error starting exam: {str(e)}')
        return redirect('dashboard:my_quizzes')


@login_required(login_url='auth:signupin')
def exam_session(request, session_id):
    """
    Display the exam interface for an active session
    """
    print(f"DEBUG: exam_session called with session_id={session_id}, user={request.user}")
    try:
        from .models import ExamSession, ExamAnswer
        from apps.brain.models import QuestionAnswer

        # Get exam session
        exam_session = get_object_or_404(ExamSession, session_id=session_id, user=request.user)
        print(f"DEBUG: Found exam session: {exam_session}, status: {exam_session.status}")

        # Check if session is still active
        if exam_session.status != 'active':
            print(f"DEBUG: Session not active (status: {exam_session.status}), redirecting to exam_result")
            return redirect('dashboard:exam_result', session_id=session_id)

        # Check if session has expired
        if exam_session.is_expired():
            print(f"DEBUG: Session expired, marking as expired and redirecting")
            exam_session.status = 'expired'
            exam_session.completed_at = timezone.now()
            exam_session.calculate_score()
            exam_session.save()
            return redirect('dashboard:exam_result', session_id=session_id)

        # Get current question
        current_index = exam_session.current_question_index
        print(f"DEBUG: Current question index: {current_index}, Total questions: {len(exam_session.questions_order)}")
        print(f"DEBUG: Questions order: {exam_session.questions_order}")

        if current_index >= len(exam_session.questions_order):
            # All questions completed
            print(f"DEBUG: All questions completed, marking exam as completed")
            exam_session.status = 'completed'
            exam_session.completed_at = timezone.now()
            exam_session.calculate_score()
            exam_session.save()
            return redirect('dashboard:exam_result', session_id=session_id)

        question_id = exam_session.questions_order[current_index]
        print(f"DEBUG: Getting question with ID: {question_id}")
        current_question = get_object_or_404(QuestionAnswer, id=question_id)
        print(f"DEBUG: Found question: {current_question.question}")

        # Get existing answer if any
        existing_answer = ExamAnswer.objects.filter(
            exam_session=exam_session,
            question=current_question
        ).first()

        # Handle form submission
        if request.method == 'POST':
            user_answer = request.POST.get('answer', '').strip()
            action = request.POST.get('action', 'next')

            if user_answer:
                # Check if answer is correct
                is_correct = False
                print(f"DEBUG: Checking answer - Question: '{current_question.question[:50]}...', User: '{user_answer}', Type: '{current_question.question_type}', CorrectOption: '{current_question.correct_option}', Answer: '{current_question.answer}'")

                if current_question.question_type == 'MULTIPLECHOICE':
                    # For multiple choice, compare with correct_option field (A, B, C, D)
                    if current_question.correct_option:
                        is_correct = user_answer.upper().strip() == current_question.correct_option.upper().strip()
                        print(f"DEBUG: Multiple choice comparison - '{user_answer.upper().strip()}' == '{current_question.correct_option.upper().strip()}' = {is_correct}")
                    else:
                        # Fallback: compare with answer text if correct_option is not set
                        is_correct = user_answer.lower().strip() == current_question.answer.lower().strip()
                        print(f"DEBUG: Multiple choice fallback - '{user_answer.lower().strip()}' == '{current_question.answer.lower().strip()}' = {is_correct}")
                else:
                    # For short answers, simple string matching (can be enhanced)
                    is_correct = user_answer.lower().strip() in current_question.answer.lower()
                    print(f"DEBUG: Short answer comparison - '{user_answer.lower().strip()}' in '{current_question.answer.lower()}' = {is_correct}")

                print(f"DEBUG: Final is_correct = {is_correct}")

                # Save or update answer
                if existing_answer:
                    existing_answer.user_answer = user_answer
                    existing_answer.is_correct = is_correct
                    existing_answer.save()
                else:
                    ExamAnswer.objects.create(
                        exam_session=exam_session,
                        question=current_question,
                        question_index=current_index,
                        user_answer=user_answer,
                        is_correct=is_correct
                    )

            # Handle navigation
            if action == 'next' and current_index < len(exam_session.questions_order) - 1:
                exam_session.current_question_index += 1
                exam_session.save()
            elif action == 'previous' and current_index > 0 and exam_session.allow_navigation:
                exam_session.current_question_index -= 1
                exam_session.save()
            elif action == 'submit':
                exam_session.status = 'completed'
                exam_session.completed_at = timezone.now()
                exam_session.calculate_score()
                exam_session.save()
                return redirect('dashboard:exam_result', session_id=session_id)

            return redirect('dashboard:exam_session', session_id=session_id)

        # Calculate progress percentage
        progress_percentage = ((current_index + 1) / len(exam_session.questions_order)) * 100

        # Prepare context
        context = {
            'exam_session': exam_session,
            'current_question': current_question,
            'current_index': current_index,
            'total_questions': len(exam_session.questions_order),
            'existing_answer': existing_answer,
            'remaining_time': exam_session.get_remaining_time_seconds(),
            'can_go_back': current_index > 0 and exam_session.allow_navigation,
            'can_go_next': current_index < len(exam_session.questions_order) - 1,
            'is_last_question': current_index == len(exam_session.questions_order) - 1,
            'progress_percentage': round(progress_percentage, 1),
        }

        return render(request, 'exam_session.html', context)

    except Exception as e:
        print(f"DEBUG: Exception in exam_session: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        messages.error(request, f'Error in exam session: {str(e)}')
        return redirect('dashboard:my_quizzes')


@login_required(login_url='auth:signupin')
def submit_exam(request, session_id):
    """
    Submit exam and redirect to results
    """
    try:
        from .models import ExamSession

        exam_session = get_object_or_404(ExamSession, session_id=session_id, user=request.user)

        if exam_session.status == 'active':
            exam_session.status = 'completed'
            exam_session.completed_at = timezone.now()
            exam_session.calculate_score()
            exam_session.save()

        return redirect('dashboard:exam_result', session_id=session_id)

    except Exception as e:
        messages.error(request, f'Error submitting exam: {str(e)}')
        return redirect('dashboard:my_quizzes')


@login_required(login_url='auth:signupin')
def exam_result(request, session_id):
    """
    Display exam results
    """
    print(f"DEBUG: exam_result called with session_id={session_id}, user={request.user}")
    try:
        from .models import ExamSession, ExamAnswer

        exam_session = get_object_or_404(ExamSession, session_id=session_id, user=request.user)
        print(f"DEBUG: Found exam session: {exam_session}")
        print(f"DEBUG: Exam session status: {exam_session.status}")
        print(f"DEBUG: Exam session completed_at: {exam_session.completed_at}")

        if exam_session.status == 'active':
            print(f"DEBUG: Status is active, redirecting to exam_session")
            return redirect('dashboard:exam_session', session_id=session_id)

        # Get all answers
        print(f"DEBUG: Getting exam answers...")
        answers = ExamAnswer.objects.filter(exam_session=exam_session).order_by('question_index')
        print(f"DEBUG: Found {answers.count()} answers")

        # Debug each answer
        for i, answer in enumerate(answers):
            print(f"DEBUG: Answer {i+1}: Question='{answer.question.question[:50]}...', User='{answer.user_answer}', Correct='{answer.question.answer}', CorrectOption='{answer.question.correct_option}', Type='{answer.question.question_type}', IsCorrect={answer.is_correct}")

        # Calculate detailed statistics
        total_questions = exam_session.total_questions
        answered_questions = answers.count()
        correct_answers = answers.filter(is_correct=True).count()
        incorrect_answers = answered_questions - correct_answers
        print(f"DEBUG: Stats - Total: {total_questions}, Answered: {answered_questions}, Correct: {correct_answers}, Incorrect: {incorrect_answers}")

        context = {
            'exam_session': exam_session,
            'answers': answers,
            'total_questions': total_questions,
            'answered_questions': answered_questions,
            'correct_answers': correct_answers,
            'incorrect_answers': incorrect_answers,
            'unanswered_questions': total_questions - answered_questions,
        }

        print(f"DEBUG: Rendering exam_result.html template...")
        return render(request, 'exam_result.html', context)

    except Exception as e:
        print(f"DEBUG: Exception in exam_result: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        messages.error(request, f'Error displaying exam results: {str(e)}')
        return redirect('dashboard:my_quizzes')


# ============================================================================
# FLASHCARD FUNCTIONALITY
# ============================================================================

@login_required(login_url='auth:signupin')
def start_flashcard(request, job_id):
    """
    Start a new flashcard session for a completed processing job
    """
    try:
        from apps.brain.models import ProcessingJob
        from .models import FlashcardSession, ExamConfiguration

        # Get the processing job
        job = get_object_or_404(ProcessingJob, id=job_id, user=request.user)

        if job.status != 'completed':
            messages.error(request, 'Cannot start flashcards for incomplete quiz.')
            return redirect('dashboard:my_quizzes')

        # Get questions
        qa_pairs = job.get_qa_pairs()
        if not qa_pairs.exists():
            messages.error(request, 'No questions found for this quiz.')
            return redirect('dashboard:my_quizzes')

        # Get configuration
        config = ExamConfiguration.get_current_config()

        # Create new flashcard session
        session_id = str(uuid.uuid4())
        cards_list = list(qa_pairs.values_list('id', flat=True))
        random.shuffle(cards_list)  # Randomize card order

        flashcard_session = FlashcardSession.objects.create(
            user=request.user,
            processing_job=job,
            session_id=session_id,
            total_cards=len(cards_list),
            time_per_card_seconds=config.default_flashcard_time_seconds,
            auto_advance=config.auto_advance_flashcards,
            cards_order=cards_list
        )

        return redirect('dashboard:flashcard_session', session_id=session_id)

    except Exception as e:
        messages.error(request, f'Error starting flashcards: {str(e)}')
        return redirect('dashboard:my_quizzes')


@login_required(login_url='auth:signupin')
def flashcard_session(request, session_id):
    """
    Display the flashcard interface for an active session
    """
    try:
        from .models import FlashcardSession, FlashcardProgress
        from apps.brain.models import QuestionAnswer

        # Get flashcard session
        flashcard_session = get_object_or_404(FlashcardSession, session_id=session_id, user=request.user)

        # Check if session is completed
        if flashcard_session.status != 'active':
            return redirect('dashboard:complete_flashcard', session_id=session_id)

        # Get current card
        current_index = flashcard_session.current_card_index
        if current_index >= len(flashcard_session.cards_order):
            # All cards completed
            flashcard_session.status = 'completed'
            flashcard_session.completed_at = timezone.now()
            flashcard_session.save()
            return redirect('dashboard:complete_flashcard', session_id=session_id)

        card_id = flashcard_session.cards_order[current_index]
        current_card = get_object_or_404(QuestionAnswer, id=card_id)

        # Handle form submission (next card)
        if request.method == 'POST':
            action = request.POST.get('action', 'next')
            was_skipped = action == 'skip'

            # Record progress for current card
            FlashcardProgress.objects.update_or_create(
                flashcard_session=flashcard_session,
                question=current_card,
                defaults={
                    'card_index': current_index,
                    'was_skipped': was_skipped,
                    'time_spent_seconds': 60  # Default time, can be enhanced with JS timing
                }
            )

            # Move to next card
            flashcard_session.current_card_index += 1
            flashcard_session.cards_studied += 1
            flashcard_session.save()

            # Check if this was the last card
            if flashcard_session.current_card_index >= len(flashcard_session.cards_order):
                flashcard_session.status = 'completed'
                flashcard_session.completed_at = timezone.now()
                flashcard_session.save()
                return redirect('dashboard:complete_flashcard', session_id=session_id)

            return redirect('dashboard:flashcard_session', session_id=session_id)

        # Prepare context
        context = {
            'flashcard_session': flashcard_session,
            'current_card': current_card,
            'current_index': current_index,
            'total_cards': len(flashcard_session.cards_order),
            'progress_percentage': ((current_index) / len(flashcard_session.cards_order)) * 100,
            'is_last_card': current_index == len(flashcard_session.cards_order) - 1,
        }

        return render(request, 'flashcard_session.html', context)

    except Exception as e:
        messages.error(request, f'Error in flashcard session: {str(e)}')
        return redirect('dashboard:my_quizzes')


@login_required(login_url='auth:signupin')
def complete_flashcard(request, session_id):
    """
    Display flashcard completion page and redirect to exam
    """
    try:
        from .models import FlashcardSession, ExamSession, ExamConfiguration

        flashcard_session = get_object_or_404(FlashcardSession, session_id=session_id, user=request.user)

        if flashcard_session.status == 'active':
            return redirect('dashboard:flashcard_session', session_id=session_id)

        # Check if user wants to start exam
        if request.method == 'POST':
            action = request.POST.get('action')
            if action == 'start_exam':
                # Get configuration (no attempt restrictions)
                config = ExamConfiguration.get_current_config()

                # Create new exam session (unlimited attempts)
                exam_session_id = str(uuid.uuid4())
                qa_pairs = flashcard_session.processing_job.get_qa_pairs()
                questions_list = list(qa_pairs.values_list('id', flat=True))
                random.shuffle(questions_list)

                ExamSession.objects.create(
                    user=request.user,
                    processing_job=flashcard_session.processing_job,
                    session_id=exam_session_id,
                    total_questions=len(questions_list),
                    time_limit_minutes=len(questions_list) * config.default_time_per_question_minutes,
                    allow_navigation=config.allow_question_navigation,
                    max_attempts=999,  # Unlimited
                    attempt_number=1,  # Always 1 since we don't track attempts
                    questions_order=questions_list
                )

                return redirect('dashboard:exam_session', session_id=exam_session_id)

            elif action == 'back_to_quizzes':
                return redirect('dashboard:my_quizzes')

        # Get progress statistics
        progress_records = flashcard_session.card_progress.all()
        total_time_spent = sum(p.time_spent_seconds for p in progress_records)

        context = {
            'flashcard_session': flashcard_session,
            'total_time_spent': total_time_spent,
            'cards_studied': flashcard_session.cards_studied,
            'total_cards': flashcard_session.total_cards,
            'progress_percentage': flashcard_session.get_progress_percentage(),
        }

        return render(request, 'flashcard_complete.html', context)

    except Exception as e:
        messages.error(request, f'Error completing flashcards: {str(e)}')
        return redirect('dashboard:my_quizzes')