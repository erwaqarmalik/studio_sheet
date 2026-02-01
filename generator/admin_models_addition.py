# This file contains the code to add to models.py after the DeletionHistory class

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
