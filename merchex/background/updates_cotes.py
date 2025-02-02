import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BDD.settings')
django.setup()

from .odds_calculator import calculer_cotes
from listings.models import Match
from django.utils import timezone

def update_all_cotes():
    today = timezone.now().date()
    matches = Match.objects.filter(date__gte=today)
    
    for match in matches:
        calculer_cotes(match.id)

if __name__ == '__main__':
    update_all_cotes()