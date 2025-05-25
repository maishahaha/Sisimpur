from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('coming-soon/', views.coming_soon, name='coming_soon'),
    path('submit-and-subscribe/', views.submit_and_subscribe, name='submit_and_subscribe'),
]