"""
Management command to restore soft-deleted records.
Usage: python manage.py restore_deleted --model=PhotoGeneration --id=123
"""
from django.core.management.base import BaseCommand, CommandError
from generator.models import PhotoGeneration, GenerationAudit


class Command(BaseCommand):
    help = 'Restore soft-deleted records'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            required=True,
            choices=['PhotoGeneration', 'GenerationAudit'],
            help='Model to restore from'
        )
        parser.add_argument(
            '--id',
            type=int,
            help='Primary key of the record to restore (omit to list all deleted)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Restore all soft-deleted records of the specified model'
        )
        parser.add_argument(
            '--reason',
            type=str,
            default='Restored via management command',
            help='Reason for restoration'
        )
    
    def handle(self, *args, **options):
        model_name = options['model']
        record_id = options['id']
        restore_all = options['all']
        reason = options['reason']
        
        # Get the model class
        model_map = {
            'PhotoGeneration': PhotoGeneration,
            'GenerationAudit': GenerationAudit,
        }
        model_class = model_map[model_name]
        
        # List mode
        if not record_id and not restore_all:
            deleted = model_class.all_objects.filter(deleted_at__isnull=False)
            count = deleted.count()
            
            if count == 0:
                self.stdout.write(self.style.WARNING(f'No soft-deleted {model_name} records found'))
                return
            
            self.stdout.write(self.style.SUCCESS(f'\nFound {count} soft-deleted {model_name} records:\n'))
            
            for obj in deleted[:20]:  # Show first 20
                self.stdout.write(
                    f'  ID: {obj.pk} | Deleted: {obj.deleted_at.strftime("%Y-%m-%d %H:%M")} | '
                    f'By: {obj.deleted_by.username if obj.deleted_by else "Unknown"} | {str(obj)[:50]}'
                )
            
            if count > 20:
                self.stdout.write(f'\n... and {count - 20} more')
            
            self.stdout.write(
                self.style.WARNING(
                    f'\nTo restore a specific record: python manage.py restore_deleted --model={model_name} --id=<ID>'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    f'To restore all: python manage.py restore_deleted --model={model_name} --all'
                )
            )
            return
        
        # Restore all mode
        if restore_all:
            deleted = model_class.all_objects.filter(deleted_at__isnull=False)
            count = deleted.count()
            
            if count == 0:
                self.stdout.write(self.style.WARNING(f'No soft-deleted {model_name} records found'))
                return
            
            confirm = input(f'\n⚠️  About to restore {count} {model_name} records. Continue? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR('Restoration cancelled'))
                return
            
            restored_count = 0
            for obj in deleted:
                try:
                    obj.restore(restored_by=None, reason=reason)
                    restored_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to restore {obj.pk}: {str(e)}'))
            
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Successfully restored {restored_count}/{count} {model_name} records')
            )
            return
        
        # Single record restore mode
        try:
            obj = model_class.all_objects.get(pk=record_id)
        except model_class.DoesNotExist:
            raise CommandError(f'{model_name} with ID {record_id} does not exist')
        
        if not obj.deleted_at:
            self.stdout.write(self.style.WARNING(f'{model_name} #{record_id} is not deleted'))
            return
        
        try:
            obj.restore(restored_by=None, reason=reason)
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Successfully restored {model_name} #{record_id}: {str(obj)}'
                )
            )
        except Exception as e:
            raise CommandError(f'Failed to restore record: {str(e)}')
