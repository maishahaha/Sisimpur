from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    path('help/', views.help, name='help'),

    # Brain/Quiz functionality
    path('quiz-generator/', views.quiz_generator, name='quiz_generator'),
    path('my-quizzes/', views.my_quizzes, name='my_quizzes'),
    path('quiz-results/<int:job_id>/', views.quiz_results, name='quiz_results'),

    # API endpoints for AJAX (Document Processing Only)
    path('api/process-document/', views.api_process_document, name='api_process_document'),
    path('api/job-status/<int:job_id>/', views.api_job_status, name='api_job_status'),
]