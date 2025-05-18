from django.urls import path
from . import views

app_name = 'auth'

urlpatterns = [
    path('', views.signupin, name='signupin'),

    # Placeholder URLs for authentication (to be implemented)
    path('login/', views.index, name='login'),
    path('register/', views.index, name='register'),
    path('password-reset/', views.index, name='password_reset'),
]
