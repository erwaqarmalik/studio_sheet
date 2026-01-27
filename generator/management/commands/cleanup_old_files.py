"""
Management command to clean up old generated files.
Run with: python manage.py cleanup_old_files
"""
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Delete generated files older than configured hours'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=None,
            help='Files older than this many hours will be deleted (defaults to FILE_CLEANUP_HOURS setting)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
    
    def handle(self, *args, **options):
        hours = options['hours'] or settings.FILE_CLEANUP_HOURS
        dry_run = options['dry_run']
        
        cutoff_time = time.time() - (hours * 3600)
        outputs_dir = Path(settings.MEDIA_ROOT) / 'outputs'
        
        if not outputs_dir.exists():
            self.stdout.write(self.style.WARNING(f'Output directory does not exist: {outputs_dir}'))
            return
        
        deleted_count = 0
        deleted_size = 0
        
        self.stdout.write(f'Cleaning up files older than {hours} hours...')
        self.stdout.write(f'Cutoff time: {datetime.fromtimestamp(cutoff_time)}')
        
        # Iterate through session folders
        for session_dir in outputs_dir.iterdir():
            if not session_dir.is_dir():
                continue
            
            # Check folder modification time
            dir_mtime = session_dir.stat().st_mtime
            
            if dir_mtime < cutoff_time:
                # Calculate size
                dir_size = sum(f.stat().st_size for f in session_dir.rglob('*') if f.is_file())
                
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Would delete: {session_dir.name} '
                            f'({self._format_size(dir_size)}, '
                            f'age: {self._format_age(dir_mtime)})'
                        )
                    )
                else:
                    try:
                        # Delete all files in directory
                        for file_path in session_dir.rglob('*'):
                            if file_path.is_file():
                                file_path.unlink()
                        
                        # Delete directory
                        session_dir.rmdir()
                        
                        deleted_count += 1
                        deleted_size += dir_size
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Deleted: {session_dir.name} '
                                f'({self._format_size(dir_size)}, '
                                f'age: {self._format_age(dir_mtime)})'
                            )
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Error deleting {session_dir.name}: {e}')
                        )
        
        # Summary
        if dry_run:
            self.stdout.write(self.style.WARNING('\n=== DRY RUN - No files were actually deleted ==='))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: {"Would delete" if dry_run else "Deleted"} '
                f'{deleted_count} session(s), freed {self._format_size(deleted_size)}'
            )
        )
    
    def _format_size(self, size_bytes):
        """Format byte size to human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f'{size_bytes:.2f} {unit}'
            size_bytes /= 1024.0
        return f'{size_bytes:.2f} TB'
    
    def _format_age(self, timestamp):
        """Format timestamp age to human-readable string."""
        age_seconds = time.time() - timestamp
        age_hours = age_seconds / 3600
        
        if age_hours < 24:
            return f'{age_hours:.1f} hours'
        else:
            age_days = age_hours / 24
            return f'{age_days:.1f} days'
