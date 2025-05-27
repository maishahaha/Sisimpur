from django.urls import path
from . import views

app_name = "brain"

urlpatterns = [
    # Document processing endpoints
    path('process/document/', views.process_document, name='process_document'),
    path('process/text/', views.process_text, name='process_text'),
    
    # Job management endpoints
    path('jobs/', views.list_jobs, name='list_jobs'),
    path('jobs/<int:job_id>/status/', views.get_job_status, name='job_status'),
    path('jobs/<int:job_id>/results/', views.get_job_results, name='job_results'),
    path('jobs/<int:job_id>/download/', views.download_results, name='download_results'),
]
