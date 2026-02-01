"""
URL configuration for passport photo generator.
"""
from django.urls import path
from .views import index
from .auth_views import (
    user_login, user_logout, history, profile,
    soft_delete_generation, restore_generation, deletion_history_view
)
from .api_views import remove_background_api

app_name = 'generator'

urlpatterns = [
    path("", index, name="index"),
    path("login/", user_login, name="login"),
    path("logout/", user_logout, name="logout"),
    path("history/", history, name="history"),
    path("history/deletion/", deletion_history_view, name="deletion_history"),
    path("profile/", profile, name="profile"),
    path("api/remove-background/", remove_background_api, name="remove_background_api"),
    path("api/delete/<int:generation_id>/", soft_delete_generation, name="soft_delete"),
    path("api/restore/<int:generation_id>/", restore_generation, name="restore"),
]
