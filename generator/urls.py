"""
URL configuration for passport photo generator.
"""
from django.urls import path
from .views import index
from .auth_views import (
    user_login, user_logout, history, profile,
    soft_delete_generation, admin_dashboard, generation_status,
    create_user, manage_users
)
from .api_views import remove_background_api, remove_background_status

app_name = 'generator'

urlpatterns = [
    path("", index, name="index"),
    path("login/", user_login, name="login"),
    path("logout/", user_logout, name="logout"),
    path("history/", history, name="history"),
    path("profile/", profile, name="profile"),
    path("admin/dashboard/", admin_dashboard, name="admin_dashboard"),
    path("admin/users/", manage_users, name="manage_users"),
    path("admin/users/create/", create_user, name="create_user"),
    path("api/remove-background/", remove_background_api, name="remove_background_api"),
    path("api/remove-background/status/<str:task_id>/", remove_background_status, name="remove_background_status"),
    path("api/generation-status/<str:session_id>/", generation_status, name="generation_status"),
    path("api/delete/<int:generation_id>/", soft_delete_generation, name="soft_delete"),]