from django.core.management.base import BaseCommand
from django.utils import timezone
from listings.models import UserLoginTracker

class Command(BaseCommand):
    help = 'Reset all user login counters'

    def handle(self, *args, **options):
        today = timezone.now().date()
        UserLoginTracker.objects.all().update(
            daily_login_count=0,
            last_reset=today
        )