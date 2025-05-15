from django.urls import path
from . import views

urlpatterns = [
    path('', views.coming_soon, name='coming_soon'),
    path('api/subscribe/', views.subscribe_to_mailchimp, name='subscribe'),
]
