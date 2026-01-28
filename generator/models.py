"""
Models for passport photo generator with user authentication.
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import RegexValidator


class UserProfile(models.Model):
    """
    Extended user profile with additional fields.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        help_text="Link to Django User"
    )
    
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text="User's date of birth"
    )
    
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Enter a valid phone number (9-15 digits, optional +)',
            )
        ],
        help_text="Phone number (10-15 digits)"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the profile was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last profile update"
    )
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.user.username})"


class PhotoGeneration(models.Model):
    """
    Record of a passport photo generation request.
    Tracks user history of generated photo sheets.
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
