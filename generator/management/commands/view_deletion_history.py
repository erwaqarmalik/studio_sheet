"""
Management command to view deletion history.
Usage: python manage.py view_deletion_history
"""
from django.core.management.base import BaseCommand
from generator.models import DeletionHistory
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'View deletion and restoration history'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            help='Filter by model name (e.g., PhotoGeneration)'
        )
        parser.add_argument(
            '--action',
            type=str,
            choices=['deleted', 'restored', 'hard_deleted'],
            help='Filter by action type'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Show history for last N days (default: 30)'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Filter by username'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maximum number of records to show (default: 50)'
        )
    
    def handle(self, *args, **options):
        model_name = options.get('model')
        action = options.get('action')
        days = options['days']
        username = options.get('user')
        limit = options['limit']
        
        # Build query
        since_date = timezone.now() - timedelta(days=days)
        history = DeletionHistory.objects.filter(performed_at__gte=since_date)
        
        if model_name:
            history = history.filter(model_name=model_name)
        
        if action:
            history = history.filter(action=action)
        
        if username:
            history = history.filter(performed_by__username=username)
        
        count = history.count()
        
        if count == 0:
            self.stdout.write(self.style.WARNING('No deletion history found for the specified criteria'))
            return
        
        # Display summary
        self.stdout.write(self.style.SUCCESS(f'\n📊 Deletion History Summary (Last {days} days)'))
        self.stdout.write(f'Total records: {count}\n')
        
        # Action breakdown
        actions_summary = history.values('action').annotate(
            count=models.Count('id')
        ).order_by('-count')
        
        from django.db import models
        
        self.stdout.write('Actions:')
        for item in actions_summary:
            self.stdout.write(f'  {item["action"]}: {item["count"]}')
        
        # Model breakdown
        models_summary = history.values('model_name').annotate(
            count=models.Count('id')
        ).order_by('-count')
        
        self.stdout.write('\nModels:')
        for item in models_summary:
            self.stdout.write(f'  {item["model_name"]}: {item["count"]}')
        
        # Recent history
        self.stdout.write(f'\n📜 Recent History (showing up to {limit} records):\n')
        
        action_icons = {
            'deleted': '🗑️',
            'restored': '♻️',
            'hard_deleted': '⚠️',
        }
        
        for record in history[:limit]:
            icon = action_icons.get(record.action, '•')
            user_str = record.performed_by.username if record.performed_by else 'System'
            
            self.stdout.write(
                f'{icon} {record.performed_at.strftime("%Y-%m-%d %H:%M")} | '
                f'{record.model_name}#{record.object_id} | '
                f'{record.action.upper()} by {user_str}'
            )
            
            if record.reason:
                self.stdout.write(f'   Reason: {record.reason[:100]}')
        
        if count > limit:
            self.stdout.write(f'\n... and {count - limit} more records')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Displayed {min(count, limit)} of {count} total records'
            )
        )
