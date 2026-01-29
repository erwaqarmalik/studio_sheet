from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, PhotoGeneration, UserRateLimit, GenerationAudit, FeatureUsage, PhotoConfiguration


class UserProfileInline(admin.StackedInline):
    """Inline editor for UserProfile in User admin."""
    model = UserProfile
    fields = (
        'date_of_birth',
        'phone_number',
        'street_address',
        'landmark',
        'city',
        'state',
        'postal_code',
        'country',
        'profile_complete',
    )
    extra = 0
    readonly_fields = ('created_at', 'updated_at', 'profile_complete')


class UserRateLimitInline(admin.TabularInline):
    """Inline editor for UserRateLimit in User admin."""
    model = UserRateLimit
    extra = 0
    readonly_fields = ('created_at', 'last_reset')
    fields = ('generations_today', 'total_size_today_mb', 'is_blocked', 'block_reason', 'block_until')


class UserAdmin(BaseUserAdmin):
    """Extended User admin with profile and rate limit fields."""
    inlines = (UserProfileInline, UserRateLimitInline)


class PhotoConfigurationInline(admin.TabularInline):
    """Inline editor for PhotoConfiguration in PhotoGeneration admin."""
    model = PhotoConfiguration
    extra = 0
    fields = ('photo_index', 'photo_size', 'custom_width_cm', 'custom_height_cm', 'copies')
    readonly_fields = ('photo_index',)


class PhotoGenerationAdmin(admin.ModelAdmin):
    """Admin for PhotoGeneration model."""
    list_display = ('session_id', 'user', 'output_type', 'created_at', 'total_copies', 'file_size_bytes')
    list_filter = ('output_type', 'paper_size', 'created_at', 'orientation')
    search_fields = ('user__username', 'user__email', 'session_id')
    readonly_fields = ('session_id', 'created_at', 'file_size_bytes')
    fieldsets = (
        ('Session Info', {
            'fields': ('user', 'session_id', 'created_at')
        }),
        ('Input Parameters', {
            'fields': ('num_photos', 'paper_size', 'orientation', 'output_type')
        }),
        ('Output File', {
            'fields': ('output_path', 'output_url', 'file_size_bytes', 'total_copies')
        }),
    )
    inlines = (PhotoConfigurationInline,)


class UserRateLimitAdmin(admin.ModelAdmin):
    """Admin for UserRateLimit model."""
    list_display = ('user', 'generations_today', 'total_size_today_mb', 'is_blocked', 'last_reset')
    list_filter = ('is_blocked', 'last_reset')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'last_reset')
    actions = ['unblock_user']
    
    def unblock_user(self, request, queryset):
        """Action to unblock users."""
        updated = queryset.update(is_blocked=False, block_reason='')
        self.message_user(request, f'{updated} user(s) unblocked.')
    unblock_user.short_description = "Unblock selected users"


class GenerationAuditAdmin(admin.ModelAdmin):
    """Admin for GenerationAudit model."""
    list_display = ('generation', 'action', 'user', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'generation__session_id', 'ip_address')
    readonly_fields = ('timestamp', 'details')
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        """Prevent manual creation of audit logs."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of audit logs."""
        return False


class FeatureUsageAdmin(admin.ModelAdmin):
    """Admin for FeatureUsage model."""
    list_display = ('feature', 'user', 'timestamp', 'duration_seconds')
    list_filter = ('feature', 'timestamp')
    search_fields = ('user__username', 'feature')
    readonly_fields = ('timestamp', 'metadata')
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        """Prevent manual creation of feature usage records."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of feature usage records."""
        return False


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(PhotoGeneration, PhotoGenerationAdmin)
admin.site.register(PhotoConfiguration)
admin.site.register(UserRateLimit, UserRateLimitAdmin)
admin.site.register(GenerationAudit, GenerationAuditAdmin)
admin.site.register(FeatureUsage, FeatureUsageAdmin)
admin.site.register(UserProfile)
