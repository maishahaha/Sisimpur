from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    path('help/', views.help, name='help'),
]