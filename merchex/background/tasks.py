from celery import shared_task
from django.utils import timezone
from listings.models import Match
from .odds_calculator import calculer_cotes

@shared_task
def update_all_matches_cotes():
    today = timezone.now().date()
    matches = Match.objects.filter(date__gte=today)
    
    results = []
    for match in matches:
        try:
            cote1, coteN, cote2 = calculer_cotes(match.id)
            results.append({
                'match_id': match.id,
                'status': 'success',
                'cotes': (cote1, coteN, cote2)
            })
        except Exception as e:
            results.append({
                'match_id': match.id,
                'status': 'error',
                'error': str(e)
            })
    
    return results
