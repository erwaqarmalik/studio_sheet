"""
Models for passport photo generator with user authentication and enhanced profile management.
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from .mixins import SoftDeleteMixin


class UserProfile(models.Model):
    """
    Enhanced user profile with comprehensive address and personal information.
    Mandatory for all users.
    """
    COUNTRY_CHOICES = [
        ('IN', 'India'),
        ('US', 'United States'),
        ('UK', 'United Kingdom'),
        ('CA', 'Canada'),
        ('AU', 'Australia'),
        ('OTHER', 'Other'),
    ]
    
    STATE_CHOICES = [
        ('', '-- Select State --'),
        ('AP', 'Andhra Pradesh'),
        ('AR', 'Arunachal Pradesh'),
        ('AS', 'Assam'),
        ('BR', 'Bihar'),
        ('CG', 'Chhattisgarh'),
        ('GA', 'Goa'),
        ('GJ', 'Gujarat'),
        ('HR', 'Haryana'),
        ('HP', 'Himachal Pradesh'),
        ('JK', 'Jammu & Kashmir'),
        ('JH', 'Jharkhand'),
        ('KA', 'Karnataka'),
        ('KL', 'Kerala'),
        ('MP', 'Madhya Pradesh'),
        ('MH', 'Maharashtra'),
        ('MN', 'Manipur'),
        ('ML', 'Meghalaya'),
        ('MZ', 'Mizoram'),
        ('NL', 'Nagaland'),
        ('OD', 'Odisha'),
        ('PB', 'Punjab'),
        ('RJ', 'Rajasthan'),
        ('SK', 'Sikkim'),
        ('TN', 'Tamil Nadu'),
        ('TS', 'Telangana'),
        ('TR', 'Tripura'),
        ('UP', 'Uttar Pradesh'),
        ('UK', 'Uttarakhand'),
        ('WB', 'West Bengal'),
        ('DL', 'Delhi'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        help_text="Link to Django User"
    )
    
    # Personal Information
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text="User's date of birth"
    )
    
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text="Phone number in E.164 format"
    )
    
    # Address Information
    street_address = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="House number, street name"
    )
    
    landmark = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Nearby landmark for easy location"
    )
    
    city = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="City/Town"
    )
    
    state = models.CharField(
        max_length=50,
        choices=STATE_CHOICES,
        blank=True,
        default='',
        help_text="State/Province"
    )
    
    postal_code = models.CharField(
        max_length=10,
        blank=True,
        default='',
        help_text="PIN/Postal Code"
    )
    
    country = models.CharField(
        max_length=50,
        choices=COUNTRY_CHOICES,
        default='IN',
        help_text="Country"
    )
    
    # Profile Metadata
    profile_complete = models.BooleanField(
        default=False,
        help_text="Whether profile has all required fields"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the profile was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last profile update"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
            models.Index(fields=['postal_code']),
            models.Index(fields=['country', 'state']),
        ]
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.user.username})"
    
    def get_full_address(self):
        """Return formatted full address."""
        return f"{self.street_address}, {self.city}, {self.state} {self.postal_code}, {self.country}"
    
    def is_complete(self):
        """Check if all required fields are filled."""
        required_fields = [
            self.date_of_birth,
            self.phone_number,
            self.street_address,
            self.city,
            self.state,
            self.postal_code,
            self.country,
        ]
        return all(required_fields)


class PhotoGeneration(SoftDeleteMixin, models.Model):
    """
    Record of a passport photo generation request.
    Tracks user history of generated photo sheets.
    Supports soft delete - deleted records can be restored.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='photo_generations',
        null=True,
        blank=True,
        help_text="User who generated the photos (null for anonymous)"
    )
    
    session_id = models.CharField(
        max_length=64,
        unique=True,
        help_text="Unique session identifier"
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When the photos were generated"
    )
    
    # Input parameters
    num_photos = models.IntegerField(
        default=1,
        help_text="Number of input photos"
    )
    
    paper_size = models.CharField(
        max_length=20,
        default='A4',
        help_text="Paper size (A4, A3, Letter)"
    )
    
    orientation = models.CharField(
        max_length=20,
        default='portrait',
        help_text="Page orientation"
    )
    
    output_type = models.CharField(
        max_length=10,
        default='PDF',
        help_text="Output format (PDF or JPEG)"
    )
    
    # Output file
    output_path = models.CharField(
        max_length=500,
        help_text="Relative path to output file"
    )
    
    output_url = models.CharField(
        max_length=500,
        help_text="Public URL to download file"
    )

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed',
        db_index=True,
        help_text="Processing status"
    )

    task_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Background task ID (Celery)"
    )

    error_message = models.TextField(
        blank=True,
        default='',
        help_text="Error message if generation failed"
    )
    
    # Metadata
    file_size_bytes = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Size of generated file in bytes"
    )
    
    total_copies = models.IntegerField(
        default=1,
        help_text="Total number of photo copies in output"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['session_id']),
        ]
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"{user_str} - {self.output_type} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def get_age_display(self):
        """Get human-readable age of generation."""
        from django.utils.timesince import timesince
        return timesince(self.created_at)
    
    def get_file_size_display(self):
        """Get human-readable file size."""
        if not self.file_size_bytes:
            return "Unknown"
        
        size = self.file_size_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f'{size:.1f} {unit}'
            size /= 1024.0
        return f'{size:.1f} TB'


class UserRateLimit(models.Model):
    """
    Track and enforce rate limits per user to prevent abuse.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='rate_limit',
        help_text="User this rate limit applies to"
    )
    
    generations_today = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of generations today"
    )
    
    total_size_today_mb = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0)],
        help_text="Total size of generations today in MB"
    )
    
    last_reset = models.DateTimeField(
        auto_now=True,
        help_text="Last time counter was reset"
    )
    
    is_blocked = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether user is rate-limited"
    )
    
    block_reason = models.TextField(
        blank=True,
        help_text="Reason for blocking"
    )
    
    block_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the block expires"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When rate limit was created"
    )
    
    class Meta:
        verbose_name = "User Rate Limit"
        verbose_name_plural = "User Rate Limits"
    
    def __str__(self):
        return f"{self.user.username} - Generations: {self.generations_today}"
    
    def reset_if_needed(self):
        """Reset counters if 24 hours have passed."""
        from django.utils import timezone
        from datetime import timedelta
        
        if timezone.now() - self.last_reset > timedelta(hours=24):
            self.generations_today = 0
            self.total_size_today_mb = 0.0
            self.save()


class GenerationAudit(SoftDeleteMixin, models.Model):
    """
    Audit trail for all photo generation actions.
    For compliance, debugging, and analytics.
    Supports soft delete for data retention compliance.
    """
    ACTIONS = [
        ('created', 'Created'),
        ('downloaded', 'Downloaded'),
        ('deleted', 'Deleted'),
        ('expired', 'Expired & Cleaned'),
        ('failed', 'Failed'),
    ]
    
    generation = models.ForeignKey(
        PhotoGeneration,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        help_text="Generation this audit entry relates to"
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generation_audits',
        help_text="User who performed the action"
    )
    
    action = models.CharField(
        max_length=20,
        choices=ACTIONS,
        db_index=True,
        help_text="Action performed"
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the action occurred"
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the requester"
    )
    
    user_agent = models.TextField(
        blank=True,
        help_text="User agent of the requester"
    )
    
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional details about the action"
    )
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['generation', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
        verbose_name = "Generation Audit"
        verbose_name_plural = "Generation Audits"
    
    def __str__(self):
        return f"{self.generation.session_id} - {self.action} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class FeatureUsage(models.Model):
    """
    Track feature usage for analytics and insights.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feature_usage',
        help_text="User using the feature"
    )
    
    feature = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Feature name (e.g., 'crop', 'batch_upload', 'export_pdf')"
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the feature was used"
    )
    
    duration_seconds = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="How long the operation took"
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional feature-specific data"
    )
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['feature', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]
        verbose_name = "Feature Usage"
        verbose_name_plural = "Feature Usage"
    
    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous"
        return f"{user_str} - {self.feature} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class PhotoConfiguration(models.Model):
    """
    Per-photo configuration for size and copies.
    Allows each photo in a batch to have different dimensions and copy counts.
    """
    PHOTO_SIZE_CHOICES = [
        ("passport_35x45", "Passport (3.5×4.5 cm)"),
        ("passport_small", "Small Passport (2.5×3.5 cm)"),
        ("id_card", "ID Card (3.0×4.0 cm)"),
        ("visa_3x4", "Visa (3.0×4.0 cm)"),
        ("visa_4x6", "Visa Large (4.0×6.0 cm)"),
        ("uk_visa", "UK Visa (4.45×5.59 cm)"),
        ("us_visa", "US Passport (5.0×5.0 cm)"),
        ("schengen", "Schengen (3.5×4.5 cm)"),
        ("australia", "Australia (4.5×5.5 cm)"),
        ("canada", "Canada (3.5×4.5 cm)"),
        ("custom", "Custom Size"),
    ]
    
    generation = models.ForeignKey(
        PhotoGeneration,
        on_delete=models.CASCADE,
        related_name='photo_configs',
        help_text="Generation this photo belongs to"
    )
    
    photo_index = models.IntegerField(
        help_text="Index of photo in batch (0-based)"
    )
    
    photo_size = models.CharField(
        max_length=30,
        choices=PHOTO_SIZE_CHOICES,
        default="passport_35x45",
        help_text="Selected photo size preset"
    )
    
    custom_width_cm = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1.0), MaxValueValidator(20.0)],
        help_text="Custom width in cm (if photo_size is 'custom')"
    )
    
    custom_height_cm = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1.0), MaxValueValidator(20.0)],
        help_text="Custom height in cm (if photo_size is 'custom')"
    )
    
    copies = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Number of copies for this photo"
    )
    
    class Meta:
        ordering = ['generation', 'photo_index']
        indexes = [
            models.Index(fields=['generation', 'photo_index']),
        ]
        unique_together = [['generation', 'photo_index']]
    
    def __str__(self):
        return f"{self.generation.session_id} - Photo {self.photo_index} ({self.photo_size}, {self.copies} copies)"
    
    def get_actual_dimensions(self):
        """Get the actual width and height in cm."""
        if self.photo_size == "custom":
            return (self.custom_width_cm, self.custom_height_cm)
        
        from generator.config import PHOTO_SIZES
        if self.photo_size in PHOTO_SIZES:
            size_info = PHOTO_SIZES[self.photo_size]
            return (size_info["width"], size_info["height"])
        
        return None


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal handler: Create empty profile when user is created.
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def create_rate_limit(sender, instance, created, **kwargs):
    """
    Signal handler: Create rate limit when user is created.
    """
    if created:
        UserRateLimit.objects.get_or_create(user=instance)


class DeletionHistory(models.Model):
    """
    Track all soft delete and restoration operations.
    Provides audit trail for data lifecycle management.
    """
    ACTIONS = [
        ('deleted', 'Soft Deleted'),
        ('restored', 'Restored'),
        ('hard_deleted', 'Permanently Deleted'),
    ]
    
    model_name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Name of the model that was deleted/restored"
    )
    
    object_id = models.IntegerField(
        db_index=True,
        help_text="Primary key of the deleted/restored object"
    )
    
    action = models.CharField(
        max_length=20,
        choices=ACTIONS,
        db_index=True,
        help_text="Action performed (deleted/restored/hard_deleted)"
    )
    
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deletion_actions',
        help_text="User who performed the action"
    )
    
    performed_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the action was performed"
    )
    
    reason = models.TextField(
        blank=True,
        help_text="Reason for the action"
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata about the action"
    )
    
    class Meta:
        ordering = ['-performed_at']
        indexes = [
            models.Index(fields=['model_name', 'object_id', '-performed_at']),
            models.Index(fields=['performed_by', '-performed_at']),
            models.Index(fields=['action', '-performed_at']),
        ]
        verbose_name = "Deletion History"
        verbose_name_plural = "Deletion History"
    
    def __str__(self):
        user_str = self.performed_by.username if self.performed_by else "System"
        return f"{self.model_name}#{self.object_id} - {self.action} by {user_str}"
    
    def get_object(self):
        """Try to retrieve the related object."""
        try:
            from django.apps import apps
            model = apps.get_model('generator', self.model_name)
            return model.all_objects.get(pk=self.object_id)
        except Exception:
            return None


class AdminActivity(models.Model):
    """
    Track admin and user actions for monitoring dashboard
    """
    ACTION_CHOICES = [
        ('login', 'User Login'),
        ('login_failed', 'Failed Login'),
        ('delete', 'Deleted Generation'),
        ('download', 'Downloaded File'),
        ('admin_action', 'Admin Action'),
        ('system', 'System Event'),
    ]
    
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        verbose_name = "Admin Activity"
        verbose_name_plural = "Admin Activities"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]
    
    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous"
        return f"{self.action_type} - {user_str} - {self.timestamp}"


class SystemMaintenance(models.Model):
    """
    Store system maintenance schedules and settings
    """
    auto_delete_days = models.IntegerField(
        default=30, 
        help_text="Delete soft-deleted records older than N days"
    )
    last_cleanup = models.DateTimeField(null=True, blank=True)
    total_deleted_records = models.IntegerField(default=0)
    total_deleted_size_mb = models.FloatField(default=0)
    cleanup_enabled = models.BooleanField(default=True, help_text="Enable automatic cleanup")
    
    class Meta:
        verbose_name = "System Maintenance"
        verbose_name_plural = "System Maintenance"
    
    def __str__(self):
        return f"Maintenance Settings (Auto-delete: {self.auto_delete_days} days)"
    
    @staticmethod
    def get_settings():
        """Get or create system maintenance settings"""
        settings, created = SystemMaintenance.objects.get_or_create(pk=1)
        return settings
