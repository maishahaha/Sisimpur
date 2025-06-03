from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path('logout/', views.logout_redirect, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    path('help/', views.help, name='help'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),

    # Brain/Quiz functionality
    path('quiz-generator/', views.quiz_generator, name='quiz_generator'),
    path('my-quizzes/', views.my_quizzes, name='my_quizzes'),
    path('quiz-results/<int:job_id>/', views.quiz_results, name='quiz_results'),

    # Exam functionality
    path('exam/start/<int:job_id>/', views.start_exam, name='start_exam'),
    path('exam/session/<str:session_id>/', views.exam_session, name='exam_session'),
    path('exam/submit/<str:session_id>/', views.submit_exam, name='submit_exam'),
    path('exam/result/<str:session_id>/', views.exam_result, name='exam_result'),

    # Flashcard functionality
    path('flashcard/start/<int:job_id>/', views.start_flashcard, name='start_flashcard'),
    path('flashcard/session/<str:session_id>/', views.flashcard_session, name='flashcard_session'),
    path('flashcard/complete/<str:session_id>/', views.complete_flashcard, name='complete_flashcard'),

    # API endpoints for AJAX (Document Processing Only)
    path('api/process-document/', views.api_process_document, name='api_process_document'),
    path('api/job-status/<int:job_id>/', views.api_job_status, name='api_job_status'),
]