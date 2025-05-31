from django.urls import path
from . import views

app_name = "auth"

urlpatterns = [
    path("signupin/", views.signupin, name="signupin"),
    path("verify-otp/", views.verify_otp, name="verify_otp"),
    path("send-otp/", views.send_otp_ajax, name="send_otp"),
    path("verify-otp-ajax/", views.verify_otp_ajax, name="verify_otp_ajax"),
    path("logout/", views.logout_view, name="logout"),
    path("google-login/", views.google_login, name="google_login"),
    path("google-callback/", views.google_callback, name="google_callback"),
]
