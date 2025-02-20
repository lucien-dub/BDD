from django.utils import timezone
from listings.models import Match
from background.odds_calculator import calculer_cotes
from listings.models import UserLoginTracker

def update_all_cotes():
    today = timezone.now().date()
    matches = Match.objects.filter(date__gte=today)
    
    for match in matches:
        calculer_cotes(match.id)

def reset_login_counters():
    """Réinitialise tous les compteurs de connexion à minuit"""
    today = timezone.now().date()
    UserLoginTracker.objects.all().update(
        daily_login_count=0,
        last_reset=today
    )