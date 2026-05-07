"""
Django management command to clean up old/abandoned drafts.

Usage:
    python manage.py cleanup_drafts --days 30
    python manage.py cleanup_drafts --days 30 --dry-run
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from applications.scholarships.draft_models import ScholarshipFormDraft


class Command(BaseCommand):
    help = 'Clean up old/abandoned scholarship application drafts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete drafts not accessed for N days (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--incomplete-only',
            action='store_true',
            help='Only delete incomplete drafts (< 100% completion)',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        incomplete_only = options['incomplete_only']

        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=days)

        # Build query
        query = ScholarshipFormDraft.objects.filter(
            last_accessed__lt=cutoff_date
        )

        if incomplete_only:
            query = query.exclude(completion_percentage=100)

        count = query.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {count} draft(s) '
                    f'not accessed since {cutoff_date.date()}'
                )
            )
            
            # Show which drafts would be deleted
            for draft in query[:10]:  # Show first 10
                self.stdout.write(
                    f'  - {draft.student}: {draft.get_draft_type_display()} '
                    f'({draft.completion_percentage}% complete, '
                    f'last accessed {draft.last_accessed})'
                )
            
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')
        else:
            if count == 0:
                self.stdout.write(
                    self.style.SUCCESS('No drafts to delete')
                )
            else:
                # Delete drafts
                query.delete()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Deleted {count} draft(s) '
                        f'not accessed since {cutoff_date.date()}'
                    )
                )


# ===== SCHEDULED CLEANUP (Celery) =====

# Add to celery tasks if using Celery for scheduling:

"""
from celery import shared_task
from django.core.management import call_command

@shared_task
def cleanup_old_drafts():
    '''
    Clean up drafts not accessed for 30 days.
    Schedule: Run daily at 2 AM using Celery Beat
    '''
    call_command('cleanup_drafts', days=30)
    return 'Cleanup completed'
"""

# Add to celery beat schedule (celery.py):

"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'cleanup-old-drafts': {
        'task': 'scholarships.tasks.cleanup_old_drafts',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM
    },
}
"""
