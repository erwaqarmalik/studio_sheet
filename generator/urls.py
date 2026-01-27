"""
URL configuration for passport photo generator.
"""
from django.urls import path
from .views import index
from .auth_views import register, user_login, user_logout, history, profile

app_name = 'generator'

urlpatterns = [
    path("", index, name="index"),
    path("register/", register, name="register"),
    path("login/", user_login, name="login"),
    path("logout/", user_logout, name="logout"),
    path("history/", history, name="history"),
    path("profile/", profile, name="profile"),
]
