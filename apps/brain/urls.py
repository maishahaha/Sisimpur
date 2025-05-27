from django.urls import path
from . import views

app_name = "brain"

urlpatterns = [
    # Document processing endpoints (OCR + Question Generation Pipeline)
    path('process/document/', views.process_document, name='process_document'),

    # Job management endpoints
    path('jobs/', views.list_jobs, name='list_jobs'),
    path('jobs/<int:job_id>/status/', views.get_job_status, name='job_status'),
    path('jobs/<int:job_id>/results/', views.get_job_results, name='job_results'),
    path('jobs/<int:job_id>/download/', views.download_results, name='download_results'),
    path('jobs/<int:job_id>/delete/', views.delete_job, name='delete_job'),

    # Development/Testing endpoints (JSON responses)
    path('dev/test/', views.dev_test_processing, name='dev_test'),
    path('dev/jobs/', views.dev_list_jobs, name='dev_jobs'),
]
