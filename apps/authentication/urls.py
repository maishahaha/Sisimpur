from django.urls import path
from . import views

app_name = "auth"

urlpatterns = [
    path("", views.signupin, name="signupin"),
]
