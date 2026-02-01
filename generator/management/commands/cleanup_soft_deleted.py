"""
Management command to permanently delete old soft-deleted records.
Usage: python manage.py cleanup_soft_deleted --days=30
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from generator.models import PhotoGeneration, GenerationAudit, DeletionHistory


class Command(BaseCommand):
    help = 'Permanently delete records that were soft-deleted more than X days ago'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete records soft-deleted more than this many days ago (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--model',
            type=str,
            choices=['PhotoGeneration', 'GenerationAudit', 'all'],
            default='all',
            help='Which model to clean up (default: all)'
        )
    
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
