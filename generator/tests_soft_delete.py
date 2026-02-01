"""
Test soft delete functionality.
Run with: python manage.py test generator.tests_soft_delete
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from generator.models import PhotoGeneration, DeletionHistory


class SoftDeleteTestCase(TestCase):
    """Test cases for soft delete functionality."""
    
    def setUp(self):
        """Create test user and photo generation."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.generation = PhotoGeneration.objects.create(
            user=self.user,
            session_id='test_session_123',
            num_photos=5,
            paper_size='A4',
            orientation='portrait',
            output_type='PDF',
            output_path='/media/test.pdf',
            output_url='/media/test.pdf',
            total_copies=10
        )
    
    def test_soft_delete(self):
        """Test that soft delete marks record as deleted."""
        pk = self.generation.pk
        
        # Soft delete
        self.generation.delete(
            deleted_by=self.user,
            reason='Test deletion'
        )
        
        # Check that record is marked as deleted
        self.assertIsNotNone(self.generation.deleted_at)
        self.assertEqual(self.generation.deleted_by, self.user)
        self.assertEqual(self.generation.deletion_reason, 'Test deletion')
        
        # Check that record is not in default queryset
        with self.assertRaises(PhotoGeneration.DoesNotExist):
            PhotoGeneration.objects.get(pk=pk)
        
        # But exists in all_objects queryset
        obj = PhotoGeneration.all_objects.get(pk=pk)
        self.assertIsNotNone(obj.deleted_at)
    
    def test_restore(self):
        """Test that restore undeletes a record."""
        # Soft delete first
        self.generation.delete(deleted_by=self.user, reason='Test')
        pk = self.generation.pk
        
        # Verify deleted
        self.assertTrue(self.generation.is_deleted())
        
        # Restore
        self.generation.restore(
            restored_by=self.user,
            reason='Test restoration'
        )
        
        # Check that record is active again
        self.assertIsNone(self.generation.deleted_at)
        self.assertFalse(self.generation.is_deleted())
        
        # Should appear in default queryset
        obj = PhotoGeneration.objects.get(pk=pk)
        self.assertIsNone(obj.deleted_at)
    
    def test_hard_delete(self):
        """Test that hard delete permanently removes record."""
        pk = self.generation.pk
        
        # Hard delete
        self.generation.delete(hard_delete=True)
        
        # Record should not exist in any queryset
        with self.assertRaises(PhotoGeneration.DoesNotExist):
            PhotoGeneration.objects.get(pk=pk)
        
        with self.assertRaises(PhotoGeneration.DoesNotExist):
            PhotoGeneration.all_objects.get(pk=pk)
    
    def test_deletion_history_created(self):
        """Test that deletion history is created on soft delete."""
        initial_count = DeletionHistory.objects.count()
        
        # Soft delete
        self.generation.delete(deleted_by=self.user, reason='Test')
        
        # Check history was created
        self.assertEqual(DeletionHistory.objects.count(), initial_count + 1)
        
        history = DeletionHistory.objects.latest('performed_at')
        self.assertEqual(history.model_name, 'PhotoGeneration')
        self.assertEqual(history.object_id, self.generation.pk)
        self.assertEqual(history.action, 'deleted')
        self.assertEqual(history.performed_by, self.user)
    
    def test_restoration_history_created(self):
        """Test that restoration history is created on restore."""
        # Soft delete first
        self.generation.delete(deleted_by=self.user, reason='Test')
        initial_count = DeletionHistory.objects.count()
        
        # Restore
        self.generation.restore(restored_by=self.user, reason='Oops')
        
        # Check history was created
        self.assertEqual(DeletionHistory.objects.count(), initial_count + 1)
        
        history = DeletionHistory.objects.latest('performed_at')
        self.assertEqual(history.action, 'restored')
        self.assertEqual(history.performed_by, self.user)
    
    def test_only_deleted_queryset(self):
        """Test only_deleted() manager method."""
        # Create another generation (active)
        active_gen = PhotoGeneration.objects.create(
            user=self.user,
            session_id='active_session',
            num_photos=3,
            paper_size='A4',
            orientation='portrait',
            output_type='PDF',
            output_path='/media/active.pdf',
            output_url='/media/active.pdf',
            total_copies=6
        )
        
        # Soft delete the first one
        self.generation.delete(deleted_by=self.user, reason='Test')
        
        # only_deleted should only return the deleted one
        deleted_qs = PhotoGeneration.objects.only_deleted()
        self.assertEqual(deleted_qs.count(), 1)
        self.assertEqual(deleted_qs.first().pk, self.generation.pk)
        
        # Default queryset should only return the active one
        active_qs = PhotoGeneration.objects.all()
        self.assertEqual(active_qs.count(), 1)
        self.assertEqual(active_qs.first().pk, active_gen.pk)
    
    def test_cannot_restore_non_deleted(self):
        """Test that restoring a non-deleted record raises error."""
        with self.assertRaises(ValueError):
            self.generation.restore(restored_by=self.user, reason='Test')
    
    def test_is_deleted_method(self):
        """Test is_deleted() method."""
        # Initially not deleted
        self.assertFalse(self.generation.is_deleted())
        
        # After soft delete
        self.generation.delete(deleted_by=self.user, reason='Test')
        self.assertTrue(self.generation.is_deleted())
        
        # After restore
        self.generation.restore(restored_by=self.user, reason='Test')
        self.assertFalse(self.generation.is_deleted())


class DeletionHistoryTestCase(TestCase):
    """Test cases for DeletionHistory model."""
    
    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_get_object(self):
        """Test get_object() method returns related object."""
        # Create and delete a generation
        generation = PhotoGeneration.objects.create(
            user=self.user,
            session_id='test_session',
            num_photos=1,
            paper_size='A4',
            orientation='portrait',
            output_type='PDF',
            output_path='/media/test.pdf',
            output_url='/media/test.pdf',
            total_copies=1
        )
        
        generation.delete(deleted_by=self.user, reason='Test')
        
        # Get the history record
        history = DeletionHistory.objects.latest('performed_at')
        
        # get_object should return the generation
        obj = history.get_object()
        self.assertIsNotNone(obj)
        self.assertEqual(obj.pk, generation.pk)
        self.assertIsInstance(obj, PhotoGeneration)
    
    def test_string_representation(self):
        """Test __str__ method."""
        history = DeletionHistory.objects.create(
            model_name='PhotoGeneration',
            object_id=123,
            action='deleted',
            performed_by=self.user,
            reason='Test'
        )
        
        expected = 'PhotoGeneration#123 - deleted by testuser'
        self.assertEqual(str(history), expected)


print('✅ Soft delete tests defined. Run with: python manage.py test generator.tests_soft_delete')
