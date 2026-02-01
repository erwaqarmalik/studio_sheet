from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    UserProfile, PhotoGeneration, UserRateLimit, 
    GenerationAudit, FeatureUsage, PhotoConfiguration, DeletionHistory
)


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
    """Admin for PhotoGeneration model with soft delete support."""
    list_display = ('session_id', 'user', 'output_type', 'created_at', 'total_copies', 'file_size_bytes', 'deletion_status')
    list_filter = ('output_type', 'paper_size', 'created_at', 'orientation', 'deleted_at')
    search_fields = ('user__username', 'user__email', 'session_id')
    readonly_fields = ('session_id', 'created_at', 'file_size_bytes', 'deleted_at', 'deleted_by', 'deletion_reason')
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
        ('Deletion Info', {
            'fields': ('deleted_at', 'deleted_by', 'deletion_reason'),
            'classes': ('collapse',)
        }),
    )
    inlines = (PhotoConfigurationInline,)
    actions = ['soft_delete_selected', 'restore_selected', 'hard_delete_selected']
    
    def get_queryset(self, request):
        """Show all objects including soft-deleted in admin."""
        return self.model.all_objects.get_queryset()
    
    def deletion_status(self, obj):
        """Display deletion status badge."""
        if obj.deleted_at:
            return format_html(
                '<span style="color: red; font-weight: bold;">🗑️ DELETED</span>'
            )
        return format_html('<span style="color: green;">✓ Active</span>')
    deletion_status.short_description = 'Status'
    
    def soft_delete_selected(self, request, queryset):
        """Soft delete selected objects."""
        count = 0
        for obj in queryset.filter(deleted_at__isnull=True):
            obj.delete(deleted_by=request.user, reason=f'Deleted via admin by {request.user.username}')
            count += 1
        self.message_user(request, f'{count} record(s) soft deleted.')
    soft_delete_selected.short_description = "Soft delete selected items"
    
    def restore_selected(self, request, queryset):
        """Restore soft-deleted objects."""
        count = 0
        for obj in queryset.filter(deleted_at__isnull=False):
            obj.restore(restored_by=request.user, reason=f'Restored via admin by {request.user.username}')
            count += 1
        self.message_user(request, f'{count} record(s) restored.')
    restore_selected.short_description = "Restore selected items"
    
    def hard_delete_selected(self, request, queryset):
        """Permanently delete selected objects."""
        count = queryset.count()
        for obj in queryset:
            obj.hard_delete()
        self.message_user(request, f'{count} record(s) permanently deleted.')
    hard_delete_selected.short_description = "⚠️ PERMANENTLY delete selected items"


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
    """Admin for GenerationAudit model with soft delete support."""
    list_display = ('generation', 'action', 'user', 'timestamp', 'ip_address', 'deletion_status')
    list_filter = ('action', 'timestamp', 'deleted_at')
    search_fields = ('user__username', 'generation__session_id', 'ip_address')
    readonly_fields = ('timestamp', 'details', 'deleted_at', 'deleted_by', 'deletion_reason')
    date_hierarchy = 'timestamp'
    actions = ['soft_delete_selected', 'restore_selected']
    
    def get_queryset(self, request):
        """Show all objects including soft-deleted in admin."""
        return self.model.all_objects.get_queryset()
    
    def deletion_status(self, obj):
        """Display deletion status badge."""
        if obj.deleted_at:
            return format_html('<span style="color: red;">🗑️ DELETED</span>')
        return format_html('<span style="color: green;">✓ Active</span>')
    deletion_status.short_description = 'Status'
    
    def soft_delete_selected(self, request, queryset):
        """Soft delete selected objects."""
        count = 0
        for obj in queryset.filter(deleted_at__isnull=True):
            obj.delete(deleted_by=request.user, reason=f'Deleted via admin by {request.user.username}')
            count += 1
        self.message_user(request, f'{count} audit record(s) soft deleted.')
    soft_delete_selected.short_description = "Soft delete selected items"
    
    def restore_selected(self, request, queryset):
        """Restore soft-deleted objects."""
        count = 0
        for obj in queryset.filter(deleted_at__isnull=False):
            obj.restore(restored_by=request.user, reason=f'Restored via admin by {request.user.username}')
            count += 1
        self.message_user(request, f'{count} audit record(s) restored.')
    restore_selected.short_description = "Restore selected items"
    
    def has_add_permission(self, request):
        """Prevent manual creation of audit logs."""
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


@admin.register(DeletionHistory)
class DeletionHistoryAdmin(admin.ModelAdmin):
    """Admin for DeletionHistory model."""
    list_display = ('model_name', 'object_id', 'action', 'performed_by', 'performed_at', 'view_object_link')
    list_filter = ('model_name', 'action', 'performed_at')
    search_fields = ('model_name', 'object_id', 'performed_by__username', 'reason')
    readonly_fields = ('model_name', 'object_id', 'action', 'performed_by', 'performed_at', 'reason', 'metadata', 'view_object_link')
    date_hierarchy = 'performed_at'
    
    fieldsets = (
        ('Action Info', {
            'fields': ('model_name', 'object_id', 'action', 'performed_by', 'performed_at')
        }),
        ('Details', {
            'fields': ('reason', 'metadata', 'view_object_link')
        }),
    )
    
    def view_object_link(self, obj):
        """Provide link to view the related object if it exists."""
        related_obj = obj.get_object()
        if related_obj:
            try:
                url = reverse(f'admin:generator_{obj.model_name.lower()}_change', args=[obj.object_id])
                return format_html('<a href="{}" target="_blank">View {} #{}</a>', url, obj.model_name, obj.object_id)
            except Exception:
                pass
        return format_html('<span style="color: gray;">Object not found</span>')
    view_object_link.short_description = 'Related Object'
    
    def has_add_permission(self, request):
        """Prevent manual creation of deletion history."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of history records."""
        return False
