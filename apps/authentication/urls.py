from django.urls import path
from . import views

app_name = "auth"

urlpatterns = [
    path("signupin/", views.signupin, name="signupin"),
    path("google-login/", views.google_login, name="google_login"),
    path("google-callback/", views.google_callback, name="google_callback"),
]
