from django.utils import timezone
from listings.models import Match
from .odds_calculator import calculer_cotes

def update_all_cotes():
    today = timezone.now().date()
    matches = Match.objects.filter(date__gte=today)
    
    for match in matches:
        calculer_cotes(match.id)