from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/subscribe/', views.subscribe_to_mailchimp, name='subscribe'),
]
