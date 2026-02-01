"""
Management command to permanently delete old soft-deleted records.
Usage: python manage.py cleanup_soft_deleted --days=30
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
import os
from generator.models import PhotoGeneration, AdminActivity, SystemMaintenance


class Command(BaseCommand):
    help = 'Permanently delete records that were soft-deleted more than X days ago'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=None,
            help='Delete records soft-deleted more than this many days ago (uses system setting if not specified)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt'
        )
    
    def handle(self, *args, **options):
        # Get system settings
        settings = SystemMaintenance.get_settings()
        
        if not settings.cleanup_enabled:
            self.stdout.write(self.style.WARNING('Cleanup is disabled in system settings'))
            return

        # Determine days threshold
        days = options.get('days') or settings.auto_delete_days
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)

        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Find soft-deleted records
        old_deleted = PhotoGeneration.only_deleted.filter(deleted_at__lt=cutoff_date)
        count = old_deleted.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No soft-deleted records to clean up'))
            return

        self.stdout.write(f'\nFound {count} soft-deleted record(s) older than {days} days')
        self.stdout.write(f'Cutoff date: {cutoff_date}')

        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY RUN] Would delete the following records:'))
            for photo in old_deleted[:10]:
                self.stdout.write(f'  - {photo.id}: {photo.filename} (deleted: {photo.deleted_at})')
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')
            return

        # Confirm deletion
        if not force:
            response = input(f'\nPermanently delete {count} record(s)? (y/N): ')
            if response.lower() != 'y':
                self.stdout.write(self.style.WARNING('Cleanup cancelled'))
                return

        # Calculate total size and collect files to delete
        total_size_mb = 0
        deleted_count = 0
        deleted_files = []

        for photo in old_deleted:
            if photo.output_path:
                try:
                    if os.path.exists(photo.output_path):
                        size_bytes = os.path.getsize(photo.output_path)
                        total_size_mb += size_bytes / (1024 * 1024)
                        deleted_files.append(photo.output_path)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'Error checking file {photo.output_path}: {e}'))

        # Delete files
        files_deleted = 0
        for file_path in deleted_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    files_deleted += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Error deleting file {file_path}: {e}'))

        # Hard delete records from database
        deleted_count, _ = old_deleted.delete()

        # Update system maintenance stats
        settings.last_cleanup = timezone.now()
        settings.total_deleted_records += deleted_count
        settings.total_deleted_size_mb += total_size_mb
        settings.save()

        # Log the cleanup action
        try:
            system_user = User.objects.filter(is_superuser=True).first()
            AdminActivity.objects.create(
                action_type='system',
                user=system_user,
                details={
                    'action': 'cleanup_soft_deleted',
                    'deleted_records': deleted_count,
                    'deleted_files': files_deleted,
                    'size_mb': round(total_size_mb, 2),
                    'days_threshold': days,
                }
            )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Error logging cleanup action: {e}'))

        # Display results
        self.stdout.write(self.style.SUCCESS(f'\n✓ Cleanup completed successfully!'))
        self.stdout.write(f'  - Deleted {deleted_count} record(s) from database')
        self.stdout.write(f'  - Deleted {files_deleted} file(s)')
        self.stdout.write(f'  - Freed {total_size_mb:.2f} MB')
    
    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        model = options['model']
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(
            self.style.WARNING(
                f'\n{"DRY RUN - " if dry_run else ""}Cleaning up records deleted before {cutoff_date.strftime("%Y-%m-%d")}\n'
            )
        )
        
        models_to_clean = []
        if model == 'all' or model == 'PhotoGeneration':
            models_to_clean.append(('PhotoGeneration', PhotoGeneration))
        if model == 'all' or model == 'GenerationAudit':
            models_to_clean.append(('GenerationAudit', GenerationAudit))
        
        total_deleted = 0
        
        for model_name, model_class in models_to_clean:
            # Get soft-deleted records older than cutoff
            old_deleted = model_class.all_objects.filter(
                deleted_at__lt=cutoff_date,
                deleted_at__isnull=False
            )
            
            count = old_deleted.count()
            
            if count > 0:
                self.stdout.write(f'\n{model_name}:')
                self.stdout.write(f'  Found {count} records to permanently delete')
                
                if not dry_run:
                    # Create history records before deleting
                    for obj in old_deleted:
                        DeletionHistory.objects.create(
                            model_name=model_name,
                            object_id=obj.pk,
                            action='hard_deleted',
                            performed_by=None,
                            reason=f'Auto-cleanup: deleted more than {days} days ago',
                            metadata={
                                'soft_deleted_at': obj.deleted_at.isoformat(),
                                'hard_deleted_at': timezone.now().isoformat(),
                                'days_since_deletion': (timezone.now() - obj.deleted_at).days,
                                'object_str': str(obj)
                            }
                        )
                    
                    # Permanently delete
                    deleted_count = 0
                    for obj in old_deleted:
                        obj.hard_delete()
                        deleted_count += 1
                    
                    total_deleted += deleted_count
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Permanently deleted {deleted_count} {model_name} records')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  [DRY RUN] Would permanently delete {count} records')
                    )
            else:
                self.stdout.write(f'\n{model_name}: No old deleted records found')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n[DRY RUN] Would have permanently deleted {total_deleted} total records'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Successfully cleaned up {total_deleted} total records'
                )
            )
