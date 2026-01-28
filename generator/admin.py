from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, PhotoGeneration


class UserProfileInline(admin.StackedInline):
    """Inline editor for UserProfile in User admin."""
    model = UserProfile
    fields = ('date_of_birth', 'phone_number')
    extra = 0


class UserAdmin(BaseUserAdmin):
    """Extended User admin with profile fields."""
    inlines = (UserProfileInline,)


class PhotoGenerationAdmin(admin.ModelAdmin):
    """Admin for PhotoGeneration model."""
    list_display = ('user', 'output_type', 'created_at', 'total_copies')
    list_filter = ('output_type', 'created_at', 'paper_size')
    search_fields = ('user__username', 'user__email', 'session_id')
    readonly_fields = ('session_id', 'created_at', 'file_size_bytes')


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Register models
admin.site.register(PhotoGeneration, PhotoGenerationAdmin)
admin.site.register(UserProfile)
