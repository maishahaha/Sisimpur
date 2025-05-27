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

    context = {
        'job': job,
        'qa_pairs': qa_pairs
    }
    return render(request, "quiz_results.html", context)

# API endpoints for AJAX calls
@login_required(login_url='auth:signupin')
@csrf_exempt
@require_http_methods(["POST"])
def api_process_document(request):
    """
    API endpoint to process documents via AJAX (OCR + Question Generation Pipeline)
    """
    try:
        from apps.brain.views import process_document
        return process_document(request)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Brain processing not available: {str(e)}'
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