"""
Soft delete mixins and managers for models.
"""
from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    """
    Manager that excludes soft-deleted objects by default.
    """
    def get_queryset(self):
        """Only return non-deleted objects by default."""
        return super().get_queryset().filter(deleted_at__isnull=True)
    
    def with_deleted(self):
        """Include soft-deleted objects."""
        return super().get_queryset()
    
    def only_deleted(self):
        """Only return soft-deleted objects."""
        return super().get_queryset().filter(deleted_at__isnull=False)


class SoftDeleteMixin(models.Model):
    """
    Mixin to add soft delete functionality to any model.
    
    Adds:
    - deleted_at: Timestamp when object was deleted
    - deleted_by: User who deleted the object
    - deletion_reason: Reason for deletion
    
    Objects are not actually deleted from database, just marked as deleted.
    """
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When the object was soft-deleted"
    )
    
    deleted_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_deletions',
        help_text="User who deleted this object"
    )
    
    deletion_reason = models.TextField(
        blank=True,
        help_text="Reason for deletion"
    )
    
    # Default manager (excludes deleted)
    objects = SoftDeleteManager()
    
    # Manager that includes deleted objects
    all_objects = models.Manager()
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False, hard_delete=False, deleted_by=None, reason=''):
        """
        Soft delete by default. Use hard_delete=True to permanently delete.
        
        Args:
            using: Database to use
            keep_parents: Keep parent objects (unused in soft delete)
            hard_delete: If True, permanently delete from database
            deleted_by: User performing the deletion
            reason: Reason for deletion
        """
        if hard_delete:
            # Permanent deletion
            return super().delete(using=using, keep_parents=keep_parents)
        else:
            # Soft deletion
            self.deleted_at = timezone.now()
            self.deleted_by = deleted_by
            self.deletion_reason = reason
            self.save(using=using)
            
            # Create deletion history record
            self._create_deletion_history(deleted_by, reason)
    
    def restore(self, restored_by=None, reason=''):
        """
        Restore a soft-deleted object.
        
        Args:
            restored_by: User performing the restoration
            reason: Reason for restoration
        """
        if not self.deleted_at:
            raise ValueError("Object is not deleted, cannot restore")
        
        self.deleted_at = None
        self.deleted_by = None
        self.deletion_reason = ''
        self.save()
        
        # Create restoration history record
        self._create_restoration_history(restored_by, reason)
    
    def hard_delete(self):
        """
        Permanently delete the object from database.
        """
        return super().delete()
    
    def is_deleted(self):
        """Check if object is soft-deleted."""
        return self.deleted_at is not None
    
    def _create_deletion_history(self, deleted_by, reason):
        """Create a history record for deletion."""
        from .models import DeletionHistory
        DeletionHistory.objects.create(
            model_name=self.__class__.__name__,
            object_id=self.pk,
            action='deleted',
            performed_by=deleted_by,
            reason=reason,
            metadata={
                'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
                'object_str': str(self)
            }
        )
    
    def _create_restoration_history(self, restored_by, reason):
        """Create a history record for restoration."""
        from .models import DeletionHistory
        DeletionHistory.objects.create(
            model_name=self.__class__.__name__,
            object_id=self.pk,
            action='restored',
            performed_by=restored_by,
            reason=reason,
            metadata={
                'restored_at': timezone.now().isoformat(),
                'object_str': str(self)
            }
        )
